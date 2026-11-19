#!/usr/bin/env bash
# Build and deploy CivicSignal to Azure Container Apps (website + API + AI model in one container).
#
#   az login                      # once
#   ./scripts/deploy_azure.sh     # first deploy, and every update after that
#
# The first run also creates the resource group, a private container registry and the
# Container Apps environment. The image is built on this computer (Docker Desktop) from the
# clean folder made by export_container.sh (no data, no tests, no .env) and pushed to the registry. Secrets come from ~/.civicsignal/prod-secrets.env and are
# stored as Container Apps secrets - they are never printed.
set -euo pipefail
cd "$(dirname "$0")/.."

SECRETS_FILE="${SECRETS_FILE:-$HOME/.civicsignal/prod-secrets.env}"
# Azure for Students only allows a few regions (see: az policy assignment list).
# East Asia (Hong Kong) is the closest allowed region to India that runs Container Apps.
LOCATION="${LOCATION:-eastasia}"
RG=civicsignal-rg
# Standard (workload profiles) environment: the newer 'Express' mode cannot pull private images
ENVIRONMENT=civicsignal-std
APP=civicsignal

az account show -o none 2>/dev/null || { echo "Not signed in to Azure - run: az login"; exit 1; }
docker info >/dev/null 2>&1 || { echo "Docker is not running - start Docker Desktop first"; exit 1; }
[ -f "$SECRETS_FILE" ] || { echo "Missing $SECRETS_FILE"; exit 1; }
secret() { grep "^$1=" "$SECRETS_FILE" | cut -d= -f2-; }
for NAME in DATABASE_URL DATABASE_READONLY_URL JWT_SECRET_KEY; do
  [ -n "$(secret "$NAME")" ] || { echo "$NAME is missing in $SECRETS_FILE"; exit 1; }
done

SUB_ID="$(az account show --query id -o tsv)"
ACR="civicsignal$(printf '%s' "$SUB_ID" | tr -d '-' | cut -c1-8)" # registry names are global
TAG="$(date +%Y%m%d-%H%M%S)"
IMAGE="$ACR.azurecr.io/civicsignal:$TAG"

echo "1/5 Preparing Azure (the first time takes a few minutes)..."
az extension add --name containerapp --upgrade --only-show-errors -o none
for P in Microsoft.App Microsoft.ContainerRegistry Microsoft.OperationalInsights; do
  az provider register --namespace "$P" --wait -o none
done
az group show -n "$RG" -o none 2>/dev/null || az group create -n "$RG" -l "$LOCATION" -o none
az acr show -n "$ACR" -o none 2>/dev/null ||
  az acr create -n "$ACR" -g "$RG" -l "$LOCATION" --sku Basic -o none
az containerapp env show -n "$ENVIRONMENT" -g "$RG" -o none 2>/dev/null ||
  az containerapp env create -n "$ENVIRONMENT" -g "$RG" -l "$LOCATION" \
    --environment-mode WorkloadProfiles --logs-destination none -o none

echo "2/5 Making the clean build folder..."
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
./scripts/export_container.sh "$WORK/civicsignal"

# Built on this computer: Azure for Students does not allow building inside Azure (ACR Tasks).
echo "3/5 Building the container on this Mac and uploading it (15-30 minutes the first time)..."
docker build --platform linux/amd64 -t "$IMAGE" "$WORK/civicsignal"
# Big uploads can break on unstable connections: keep retrying for up to ~15 minutes of
# outages (finished layers are not re-sent)
MAX=30
for ATTEMPT in $(seq 1 $MAX); do
  az acr login -n "$ACR" --only-show-errors 2>/dev/null && docker push "$IMAGE" && break
  [ "$ATTEMPT" = "$MAX" ] && { echo "Upload failed $MAX times - check the internet and run this script again"; exit 1; }
  echo "Upload interrupted (internet hiccup?) - retrying in 30 seconds (attempt $((ATTEMPT + 1)) of $MAX)..."
  sleep 30
done

DOMAIN="$(az containerapp env show -n "$ENVIRONMENT" -g "$RG" --query properties.defaultDomain -o tsv)"
APP_URL="https://$APP.$DOMAIN"

echo "4/5 Starting the app..."
SECRETS=(
  "database-url=$(secret DATABASE_URL)"
  "database-readonly-url=$(secret DATABASE_READONLY_URL)"
  "jwt-secret-key=$(secret JWT_SECRET_KEY)"
)
ENV_VARS=(
  "DATABASE_URL=secretref:database-url"
  "DATABASE_READONLY_URL=secretref:database-readonly-url"
  "JWT_SECRET_KEY=secretref:jwt-secret-key"
  "CORS_ORIGINS=[\"$APP_URL\"]"
)
# The app pulls with the registry's own credentials (stored by Container Apps as a secret;
# never printed)
az acr update -n "$ACR" --admin-enabled true -o none
ACR_USER="$(az acr credential show -n "$ACR" --query username -o tsv)"
ACR_PASS="$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)"

# max-replicas 1: stays inside the free allowance, and the in-memory rate limiter sees every
# request. min-replicas 0: sleeps when idle.
if az containerapp show -n "$APP" -g "$RG" -o none 2>/dev/null; then
  az containerapp registry set -n "$APP" -g "$RG" --server "$ACR.azurecr.io" \
    --username "$ACR_USER" --password "$ACR_PASS" -o none
  az containerapp secret set -n "$APP" -g "$RG" --secrets "${SECRETS[@]}" -o none
  az containerapp ingress enable -n "$APP" -g "$RG" --type external --target-port 8080 -o none
  az containerapp update -n "$APP" -g "$RG" --image "$IMAGE" \
    --cpu 1.0 --memory 2.0Gi --min-replicas 0 --max-replicas 1 \
    --set-env-vars "${ENV_VARS[@]}" -o none
else
  az containerapp create -n "$APP" -g "$RG" --environment "$ENVIRONMENT" \
    --image "$IMAGE" --registry-server "$ACR.azurecr.io" \
    --registry-username "$ACR_USER" --registry-password "$ACR_PASS" \
    --ingress external --target-port 8080 \
    --cpu 1.0 --memory 2.0Gi --min-replicas 0 --max-replicas 1 \
    --secrets "${SECRETS[@]}" --env-vars "${ENV_VARS[@]}" -o none
fi
unset SECRETS ACR_PASS

echo "5/5 Removing old images (keeping the newest 2)..."
for OLD in $(az acr repository show-tags -n "$ACR" --repository civicsignal --orderby time_desc -o tsv | tail -n +3); do
  az acr repository delete -n "$ACR" --image "civicsignal:$OLD" --yes -o none
done

echo
echo "CivicSignal is live: $APP_URL"
echo "(first visit after a quiet period takes up to a minute while it wakes up)"
