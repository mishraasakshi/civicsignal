#!/usr/bin/env bash
# Build a clean folder for the Hugging Face Space (the Space's code is public).
#
#   ./scripts/export_space.sh ../civicsignal-space
#
# Includes only what the app needs to run. Never includes: data/, .env files, tests,
# git history, node_modules, virtual environments, caches.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:?usage: scripts/export_space.sh <output-folder>}"
MODEL=ml/artifacts/embed_minilm.joblib
[ -f "$MODEL" ] || { echo "Missing $MODEL - run ml/models/train_embed.py first"; exit 1; }

mkdir -p "$OUT"
# start clean, but keep the Space's own .git folder if this is an existing clone
find "$OUT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

cp deploy/huggingface/Dockerfile deploy/huggingface/start.sh deploy/huggingface/README.md "$OUT/"
rsync -a backend/ "$OUT/backend/" \
  --exclude venv --exclude __pycache__ --exclude .pytest_cache --exclude tests \
  --exclude '*.db' --exclude '.env*'
rsync -a frontend/ "$OUT/frontend/" \
  --exclude node_modules --exclude dist --exclude '.env*' --exclude '*.test.ts' --exclude '*.test.tsx'
mkdir -p "$OUT/ml/artifacts" && cp "$MODEL" "$OUT/ml/artifacts/"

# Safety checks: fail loudly if anything sensitive slipped in
if find "$OUT" -path "$OUT/.git" -prune -o \( -name '.env' -o -name '*.csv' -o -name '*.db' -o -path '*/data/*' \) -print | grep -q .; then
  echo "ERROR: sensitive-looking files found in $OUT"; exit 1
fi
if grep -rIl --exclude-dir=.git -E 'gsk_[A-Za-z0-9]{20,}|github_pat_|hf_[A-Za-z0-9]{20,}' "$OUT" | grep -q .; then
  echo "ERROR: something that looks like an API key was found in $OUT"; exit 1
fi

echo "Space folder ready: $OUT ($(find "$OUT" -path "$OUT/.git" -prune -o -type f -print | wc -l | tr -d ' ') files)"
