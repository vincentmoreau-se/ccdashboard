#!/usr/bin/env bash
# CCDashboard — install deps and start both services with a single command.
#   Backend  (FastAPI/uv) → http://localhost:8000
#   Frontend (Vite/React) → http://localhost:5173
# Stop everything with Ctrl+C.
#
# Optional central export (push aggregates to the hackathon server):
#   ./start.sh --export <URL> <TOKEN>
set -euo pipefail

cd "$(dirname "$0")"

EXPORT_ENABLED=false
CHECK_ONLY=false
ENDPOINT_ARG=""
TOKEN_ARG=""

usage() {
  cat <<'USAGE'
Usage: ./start.sh [--export <URL> <TOKEN>] [--check]

  (no args)            Run locally only — no central export.
  --export <URL> <TOKEN>
                       Push aggregates to the central ingest endpoint <URL>
                       (e.g. https://<host>/ccdash/ingest) using <TOKEN> as the
                       bearer. Either value may instead be supplied via the
                       CCDASH_EXPORT_ENDPOINT / CCDASH_EXPORT_TOKEN env vars.
  --check              Print the resolved configuration and exit (no install/run).
  -h, --help           Show this help.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --export)
      EXPORT_ENABLED=true; shift
      # Take up to two following non-flag args: <URL> then <TOKEN>.
      if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then ENDPOINT_ARG="$1"; shift; fi
      if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then TOKEN_ARG="$1"; shift; fi
      ;;
    --check) CHECK_ONLY=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "✗ Unknown argument: $1"; echo; usage; exit 2 ;;
  esac
done

if [ "$EXPORT_ENABLED" = true ]; then
  export CCDASH_EXPORT_ENABLED=true
  [ -n "$ENDPOINT_ARG" ] && export CCDASH_EXPORT_ENDPOINT="$ENDPOINT_ARG"
  [ -n "$TOKEN_ARG" ] && export CCDASH_EXPORT_TOKEN="$TOKEN_ARG"
  if [ -z "${CCDASH_EXPORT_ENDPOINT:-}" ] || [ -z "${CCDASH_EXPORT_TOKEN:-}" ]; then
    echo "✗ --export requires both an ingest URL and a token."
    echo "  Inline:  ./start.sh --export <URL> <TOKEN>"
    echo "  Env:     CCDASH_EXPORT_ENDPOINT=<URL> CCDASH_EXPORT_TOKEN=<TOKEN> ./start.sh --export"
    exit 1
  fi
  echo "▶ Central export ENABLED → $CCDASH_EXPORT_ENDPOINT (token: ***hidden***)"
else
  echo "▶ Central export disabled (local only) — use --export to push to the server."
fi

if [ "$CHECK_ONLY" = true ]; then
  echo "▶ --check: configuration resolved, exiting before install/launch."
  exit 0
fi

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
