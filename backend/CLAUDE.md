# Backend (FastAPI)

Parses Claude Code session `.jsonl` files into aggregates and serves them.
Import root is `app`; run all commands from `backend/`.

## Tooling: uv only

System Python is externally-managed — **never** `pip install`. Use uv:

```bash
uv sync                              # install/refresh deps + uv.lock
uv run pytest -q                     # full suite
uv run pytest tests/test_x.py -v     # focused
uv run uvicorn app.main:app --port 8000 --reload
```

## Module map (one responsibility each)

| File | Responsibility |
|---|---|
| `config.py` | `Settings` (env prefix `CCDASH_`), `get_settings()` (lru_cache) |
| `models.py` | Pydantic v2: `Usage`, `MessageRecord`, `SessionSummary`, `ProjectSummary`, `ModelStat`, `TimeBucket`, `Overview` |
| `parser.py` | `parse_session_file` / `parse_lines` → `ParsedSession` |
| `pricing.py` | `PriceTable` (loads `../pricing.json`), `detect_provider` |
| `summary.py` | `summarize_session` → one `SessionSummary` |
| `store.py` | `SessionStore`: mtime-keyed cache over parse+summarize |
| `metrics.py` | `build_overview`, `list_projects`, `project_detail` |
| `main.py` | FastAPI routes + `get_store` dependency |
| `watcher.py` | live: `active_sessions`, `live_snapshot` (polling) |
| `exporter.py` | optional periodic push of aggregates |

## Conventions & invariants

- **Cost:** `PriceTable.cost_for_usage` returns `(cost, known)`. `known=False`
  for an unmissed model entry (cost `0.0`); `cost_known` is AND-reduced through
  session→project→overview. Never report unknown cost as known.
- **Provider** is resolved once, from the *first* assistant model with a model id.
- **Resilience:** malformed JSONL lines are counted (`skipped_lines`), not fatal;
  missing `usage`/nested keys coalesce to 0; `all_summaries` skips `OSError` files.
- **Live uses periodic polling** (~2s full snapshot), a deliberate simplification
  — no filesystem watcher.
- **Sort keys** over timestamps use tuple keys so missing timestamps never raise.
- **Tests are behavior-first:** real fixtures via `TestClient`, `httpx.MockTransport`
  for the exporter; an autouse fixture clears `app.dependency_overrides`. Keep
  test output pristine.

## API surface

`GET /api/health`, `/api/config`, `/api/overview`, `/api/projects`,
`/api/projects/{project}`, `/api/sessions/{session_id}`, `/api/live` (SSE).
CORS is scoped to the local frontend origin.

## Config (env `CCDASH_*`)

`projects_dir`, `currency`, `pricing_path`, `default_provider`,
`live_active_threshold_seconds`, and `export_*` (`enabled` default false,
`endpoint`, `token`, `interval_minutes`, `include_enriched`, `machine_id`,
`user_id`, `instance_id`). Export sends aggregates only unless
`include_enriched=true`; failures are logged (status only, never the token)
and retried next cycle.
