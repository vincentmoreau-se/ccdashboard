#!/usr/bin/env bash
# CCDashboard — install deps and start both services with a single command.
# Backend (FastAPI/uv) and frontend (Vite/React) bind to RANDOM free localhost
# ports (not the usual 8000/5173) to avoid clashing with other dev servers; the
# script prints the IHM URL to open. Stop everything with Ctrl+C.
# Override ports with CCDASH_BACKEND_PORT / CCDASH_FRONTEND_PORT if needed.
#
# Optional central export (push aggregates to the hackathon server):
#   ./start.sh --export <URL> <TOKEN>
set -euo pipefail

cd "$(dirname "$0")"

# Ports currently in LISTEN state (from `ss`; empty if ss is unavailable).
USED_PORTS="$( (ss -ltnH 2>/dev/null || true) | awk '{print $4}' | grep -oE '[0-9]+$' | sort -u)"

# Echo a random free port in 30000–49999 (optionally avoiding $1).
pick_port() {
  local p
  for _ in $(seq 1 100); do
    p=$(( (RANDOM % 20000) + 30000 ))
    [ "${1:-}" = "$p" ] && continue
    printf '%s\n' "$USED_PORTS" | grep -qx "$p" && continue
    echo "$p"; return 0
  done
  echo "✗ could not find a free port" >&2; return 1
}

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
  --check              Print the resolved configuration (incl. chosen ports)
                       and exit (no install/run).
  -h, --help           Show this help.

Ports: random free localhost ports are chosen at each launch (the IHM URL is
printed). Pin them with CCDASH_BACKEND_PORT / CCDASH_FRONTEND_PORT.
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
  # Push often enough to stay inside the server's ~120s live window so in-progress
  # sessions show up on the central Flight Deck. Override with the env var.
  export CCDASH_EXPORT_INTERVAL_SECONDS="${CCDASH_EXPORT_INTERVAL_SECONDS:-30}"
  if [ -z "${CCDASH_EXPORT_ENDPOINT:-}" ] || [ -z "${CCDASH_EXPORT_TOKEN:-}" ]; then
    echo "✗ --export requires both an ingest URL and a token."
    echo "  Inline:  ./start.sh --export <URL> <TOKEN>"
    echo "  Env:     CCDASH_EXPORT_ENDPOINT=<URL> CCDASH_EXPORT_TOKEN=<TOKEN> ./start.sh --export"
    exit 1
  fi
  echo "▶ Central export ENABLED → $CCDASH_EXPORT_ENDPOINT (token: ***hidden***, every ${CCDASH_EXPORT_INTERVAL_SECONDS}s)"
else
  echo "▶ Central export disabled (local only) — use --export to push to the server."
fi

BACKEND_PORT="${CCDASH_BACKEND_PORT:-$(pick_port)}"
FRONTEND_PORT="${CCDASH_FRONTEND_PORT:-$(pick_port "$BACKEND_PORT")}"
echo "▶ Local IHM → http://localhost:$FRONTEND_PORT   (backend API → http://localhost:$BACKEND_PORT)"

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

echo "▶ Starting backend on http://localhost:$BACKEND_PORT"
( cd backend && uv run uvicorn app.main:app --port "$BACKEND_PORT" ) &
BACKEND_PID=$!

# Kill the backend when this script exits (Ctrl+C in the foreground frontend, or error).
trap 'echo; echo "⏹ Stopping…"; kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

cat <<BANNER

────────────────────────────────────────────────────────────
  ✅ CCDashboard is starting
     ▸ Open your local IHM →  http://localhost:$FRONTEND_PORT
       (backend API           http://localhost:$BACKEND_PORT)
     Press Ctrl+C to stop.
────────────────────────────────────────────────────────────
BANNER

# Point the SPA at the backend's (random) port; CORS allows any localhost origin.
( cd frontend && VITE_API_BASE="http://localhost:$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" --strictPort )
