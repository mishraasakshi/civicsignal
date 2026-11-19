#!/usr/bin/env bash
# Run one command against the PRODUCTION database (Neon), using the URLs saved in
# ~/.civicsignal/prod-secrets.env. Values are never printed.
#
#   ./scripts/with_prod_db.sh backend/venv/bin/python backend/scripts/create_supervisor.py --email you@example.com
#   ./scripts/with_prod_db.sh backend/venv/bin/python backend/scripts/import_group_summaries.py
set -euo pipefail
cd "$(dirname "$0")/.."
SECRETS_FILE="${SECRETS_FILE:-$HOME/.civicsignal/prod-secrets.env}"
[ -f "$SECRETS_FILE" ] || { echo "Missing $SECRETS_FILE"; exit 1; }
[ $# -gt 0 ] || { echo "usage: scripts/with_prod_db.sh <command> [args...]"; exit 1; }

DATABASE_URL="$(grep '^DATABASE_URL=' "$SECRETS_FILE" | cut -d= -f2-)"
DATABASE_READONLY_URL="$(grep '^DATABASE_READONLY_URL=' "$SECRETS_FILE" | cut -d= -f2-)"
export DATABASE_URL DATABASE_READONLY_URL
echo "(using the production database)"
exec "$@"
