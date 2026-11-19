#!/bin/sh
# Container start: check settings, bring the database schema up to date, start the server.
set -e
cd /app
# 1) refuse to start with weak or missing secrets (before touching the database)
PYTHONPATH=backend python -c "from app.core.config import settings; from app.core.production_checks import enforce; enforce(settings)"
# 2) create / update tables
python -m alembic -c backend/alembic.ini upgrade head
# 3) serve the website + API
exec python -m uvicorn app.main:app --app-dir backend \
  --host 0.0.0.0 --port "${PORT:-7860}" --no-server-header
