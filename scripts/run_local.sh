#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn is not installed. Run: python3 -m pip install -r requirements.txt"
  exit 1
fi

if [ ! -d "$ROOT_DIR/frontend" ]; then
  echo "Frontend directory not found."
  exit 1
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "Frontend dependencies missing. Run: cd frontend && npm install"
  exit 1
fi

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd "$ROOT_DIR/frontend"
npm run dev -- --host 0.0.0.0

wait "$BACKEND_PID"
