# CCDashboard

Local web dashboard to monitor and understand local Claude Code sessions
(cost/tokens, per-project activity, session timeline, live monitoring).

## Architecture

Two services, developed independently, in their own subdirectories:

- `backend/` — FastAPI (Python, **uv**). Reads `~/.claude/projects/*/*.jsonl`,
  derives aggregates with per-model cost, serves REST + an SSE live stream.
  See `backend/CLAUDE.md`.
- `frontend/` — React + Vite + TypeScript SPA consuming that API.
  See `frontend/CLAUDE.md`.

Data flow: `*.jsonl` → backend parse/aggregate/price → REST/SSE → frontend pages
(Overview, Projects, ProjectDetail, Session, Live).

```
backend/   FastAPI app + tests          → backend/CLAUDE.md
frontend/  React SPA + unit & e2e tests → frontend/CLAUDE.md
pricing.json   per-million token prices, keyed provider→model (repo root, user-editable)
docs/superpowers/specs|plans/  authoritative design spec & implementation plan
```

## Run

Backend on :8000 and frontend on :5173, each started from its own dir — exact
commands and dev workflow live in the respective subdir `CLAUDE.md`.

## Cross-cutting conventions

- **Source of truth for behavior:** `docs/superpowers/specs/2026-06-28-ccdashboard-design.md`
  (7 sections) and the matching plan. Read the spec before changing contracts.
- **Cost is never silently zero.** An unknown model yields a cost flagged
  *unknown* end-to-end; the UI must surface it. Preserve this invariant across
  both services.
- **Frontend types mirror backend Pydantic models one-to-one.** Any field
  change in `backend/app/models.py` must be reflected in `frontend/src/api/client.ts`.
- **Currency** is backend-configurable and delivered to the frontend via
  `GET /api/config`; never hardcode a currency symbol in components.
- **Central-server export is a future project.** This repo ships only the
  exporter (disabled by default) and the documented payload contract (spec §7).
- Conventional Commits. End commit messages with the required
  `Co-Authored-By` trailer.
