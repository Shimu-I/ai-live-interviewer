#!/bin/bash
# Starts the app in dev mode with auto-reload.
# Run from the project root: ./scripts/run.sh
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate
echo "Open http://localhost:8000 in your browser (NOT 0.0.0.0 - the mic is blocked there)"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
