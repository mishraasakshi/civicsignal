#!/usr/bin/env bash
# Start the CivicSignal backend for local development.
# Auto-reloads only when backend code changes (not frontend/ or ml/ files).
set -euo pipefail
cd "$(dirname "$0")/.."
exec backend/venv/bin/uvicorn app.main:app \
  --app-dir backend \
  --reload --reload-dir backend \
  --host 127.0.0.1 --port 8000
