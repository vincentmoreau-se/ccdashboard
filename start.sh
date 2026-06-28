#!/usr/bin/env bash
# CCDashboard — install deps and start both services with a single command.
#   Backend  (FastAPI/uv) → http://localhost:8000
#   Frontend (Vite/React) → http://localhost:5173
# Stop everything with Ctrl+C.
set -euo pipefail

cd "$(dirname "$0")"

command -v uv  >/dev/null 2>&1 || { echo "✗ 'uv' is required — install: https://docs.astral.sh/uv/"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "✗ 'npm' (Node.js) is required — install: https://nodejs.org/"; exit 1; }

echo "▶ Installing backend dependencies (uv sync)…"
( cd backend && uv sync )

echo "▶ Installing frontend dependencies (npm install)…"
( cd frontend && npm install )

echo "▶ Starting backend on http://localhost:8000"
( cd backend && uv run uvicorn app.main:app --port 8000 ) &
BACKEND_PID=$!

# Kill the backend when this script exits (Ctrl+C in the foreground frontend, or error).
trap 'echo; echo "⏹ Stopping…"; kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

echo "▶ Starting frontend on http://localhost:5173 (open it in your browser)"
( cd frontend && npm run dev )
