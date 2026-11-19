#!/usr/bin/env bash
# Start the CivicSignal frontend (Vite) for local development: http://localhost:5173
set -euo pipefail
cd "$(dirname "$0")/../frontend"
exec npm run dev
