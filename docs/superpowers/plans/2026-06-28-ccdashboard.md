# CCDashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web dashboard that monitors and explains local Claude Code sessions (cost/tokens overview, per-project view, session explorer, live monitoring), with an optional periodic export of aggregates to a future central server.

**Architecture:** A FastAPI backend reads `~/.claude/projects/<project>/<session>.jsonl`, parses each line into `MessageRecord`s, derives `SessionSummary` / `ProjectSummary` aggregates (cost from a configurable price table), and serves them over REST. A file watcher pushes live updates over SSE. A React + Vite + TypeScript frontend renders four areas (Overview, Projects, Session explorer, Live). An isolated exporter periodically POSTs aggregates to a configurable endpoint.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, watchdog, httpx, Pydantic v2, pytest (backend, managed with `uv`); React 18, Vite, TypeScript, React Router, TanStack Query, Recharts, Vitest + Testing Library (frontend).

## Global Constraints

- Python managed with **uv** (system Python is externally-managed; never plain `pip install`). All backend commands run via `uv run …` from `backend/`.
- Backend package import root is `app` (run commands from `backend/`).
- Data source dir defaults to `~/.claude/projects`, overridable via config/env `CCDASH_PROJECTS_DIR`.
- Token prices in `pricing.json` are **per million tokens**, keyed `provider → model → {input, output, cache_write_5m, cache_write_1h, cache_read}`.
- Unknown model (no price entry) ⇒ cost flagged unknown, **never silently 0**.
- Export is **disabled by default** (`CCDASH_EXPORT_ENABLED=false`); aggregates only by default; enriched fields (`ai_title`, `git_branch`, `cc_version`) only when `CCDASH_EXPORT_INCLUDE_ENRICHED=true`.
- Commit after every task. Conventional commit messages.

---

## File Structure

```
backend/
  pyproject.toml                 # uv project, deps, pytest config
  app/
    __init__.py
    config.py                    # Settings (env-overridable)
    models.py                    # Pydantic: Usage, MessageRecord, SessionSummary, ProjectSummary, Overview, TimeBucket, ModelStat
    parser.py                    # parse_session_file() -> ParsedSession
    summary.py                   # summarize_session() -> SessionSummary
    pricing.py                   # PriceTable, cost_for_usage()
    store.py                     # SessionStore: mtime-keyed cache over parser+summary+pricing
    metrics.py                   # build_overview(), list_projects(), project_detail()
    watcher.py                   # active-file detection + SSE event generator
    exporter.py                  # payload build + cursor + periodic POST
    main.py                      # FastAPI app + routes wiring
  tests/
    fixtures/sample.jsonl        # representative session fixture
    fixtures/corrupt.jsonl       # malformed + missing-field lines
    test_parser.py
    test_summary.py
    test_pricing.py
    test_store.py
    test_metrics.py
    test_exporter.py
pricing.json                     # configurable price table (repo root)
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.tsx
    App.tsx                      # router + layout
    api/client.ts                # REST calls + types
    api/sse.ts                   # SSE subscription
    lib/format.ts                # token/cost/date formatting
    components/KpiCard.tsx
    components/CostTokenChart.tsx
    components/UnknownCostBadge.tsx
    pages/Overview.tsx
    pages/Projects.tsx
    pages/ProjectDetail.tsx
    pages/Session.tsx
    pages/Live.tsx
    test/format.test.ts
    test/KpiCard.test.tsx
README.md
```

---

## Task 1: Backend scaffolding & config

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/config.py`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Produces: `app.config.Settings` (Pydantic settings) and `app.config.get_settings() -> Settings`. Fields: `projects_dir: Path`, `currency: str`, `pricing_path: Path`, `default_provider: str`, `live_active_threshold_seconds: int`, `export_enabled: bool`, `export_endpoint: str | None`, `export_token: str | None`, `export_interval_minutes: int`, `export_include_enriched: bool`, `export_machine_id: str`, `export_user_id: str`, `export_instance_id: str`.

- [ ] **Step 1: Create `backend/pyproject.toml`**

```toml
[project]
name = "ccdashboard-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
    "watchdog>=4.0",
    "httpx>=0.27",
]

[dependency-groups]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `backend/app/__init__.py`** (empty file)

- [ ] **Step 3: Write `backend/app/config.py`**

```python
import socket
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CCDASH_", env_file=".env")

    projects_dir: Path = Path.home() / ".claude" / "projects"
    currency: str = "€"
    pricing_path: Path = Path(__file__).resolve().parents[2] / "pricing.json"
    default_provider: str = "anthropic"
    live_active_threshold_seconds: int = 30

    export_enabled: bool = False
    export_endpoint: str | None = None
    export_token: str | None = None
    export_interval_minutes: int = 15
    export_include_enriched: bool = False
    export_machine_id: str = socket.gethostname()
    export_user_id: str = "unknown"
    export_instance_id: str = "default"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Write the failing test `backend/tests/test_config.py`**

```python
from pathlib import Path

from app.config import Settings


def test_defaults():
    s = Settings()
    assert s.projects_dir.name == "projects"
    assert s.export_enabled is False
    assert s.currency == "€"


def test_env_override(monkeypatch):
    monkeypatch.setenv("CCDASH_PROJECTS_DIR", "/tmp/x")
    monkeypatch.setenv("CCDASH_EXPORT_ENABLED", "true")
    s = Settings()
    assert s.projects_dir == Path("/tmp/x")
    assert s.export_enabled is True
```

- [ ] **Step 5: Run tests, expect PASS**

Run: `cd backend && uv run pytest tests/test_config.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/config.py backend/tests/test_config.py backend/uv.lock
git commit -m "feat(backend): scaffold project and config"
```

---

## Task 2: Data models

**Files:**
- Create: `backend/app/models.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces:
  - `Usage(input:int=0, output:int=0, cache_write_5m:int=0, cache_write_1h:int=0, cache_read:int=0, web_search:int=0, web_fetch:int=0)` with method `add(other: Usage) -> Usage`.
  - `MessageRecord(uuid, parent_uuid, timestamp: datetime|None, type: str, model: str|None, git_branch, cwd, cc_version, usage: Usage, tools: list[str], content_kinds: list[str])`.
  - `SessionSummary(session_id, project, cwd, file_path, ai_title, started_at, ended_at, duration_seconds, is_active, models: list[str], provider, git_branch, cc_version, message_count, usage: Usage, cost: float, cost_known: bool, tool_counts: dict[str,int], skipped_lines: int)`.
  - `ProjectSummary(name, path, session_count, usage: Usage, cost: float, cost_known: bool, last_activity: datetime|None, models: list[str])`.
  - `ModelStat(model, provider, usage: Usage, cost: float, cost_known: bool, session_count: int)`.
  - `TimeBucket(date: str, session_count: int, usage: Usage, cost: float)`.
  - `Overview(session_count, total_usage: Usage, total_cost, cost_known, by_model: list[ModelStat], by_project: list[ProjectSummary], timeseries: list[TimeBucket])`.

- [ ] **Step 1: Write the failing test `backend/tests/test_models.py`**

```python
from app.models import Usage


def test_usage_add():
    a = Usage(input=10, output=5, cache_read=2)
    b = Usage(input=1, output=1, web_search=3)
    c = a.add(b)
    assert c.input == 11
    assert c.output == 6
    assert c.cache_read == 2
    assert c.web_search == 3
```

- [ ] **Step 2: Run test, expect FAIL** (`ModuleNotFoundError: app.models`)

Run: `cd backend && uv run pytest tests/test_models.py -v`

- [ ] **Step 3: Write `backend/app/models.py`**

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Usage(BaseModel):
    input: int = 0
    output: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    web_search: int = 0
    web_fetch: int = 0

    def add(self, other: "Usage") -> "Usage":
        return Usage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_write_5m=self.cache_write_5m + other.cache_write_5m,
            cache_write_1h=self.cache_write_1h + other.cache_write_1h,
            cache_read=self.cache_read + other.cache_read,
            web_search=self.web_search + other.web_search,
            web_fetch=self.web_fetch + other.web_fetch,
        )


class MessageRecord(BaseModel):
    uuid: str | None = None
    parent_uuid: str | None = None
    timestamp: datetime | None = None
    type: str
    model: str | None = None
    git_branch: str | None = None
    cwd: str | None = None
    cc_version: str | None = None
    usage: Usage = Field(default_factory=Usage)
    tools: list[str] = Field(default_factory=list)
    content_kinds: list[str] = Field(default_factory=list)


class SessionSummary(BaseModel):
    session_id: str
    project: str
    cwd: str | None = None
    file_path: str
    ai_title: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: float | None = None
    is_active: bool = False
    models: list[str] = Field(default_factory=list)
    provider: str = "anthropic"
    git_branch: str | None = None
    cc_version: str | None = None
    message_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0
    cost_known: bool = True
    tool_counts: dict[str, int] = Field(default_factory=dict)
    skipped_lines: int = 0


class ProjectSummary(BaseModel):
    name: str
    path: str
    session_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0
    cost_known: bool = True
    last_activity: datetime | None = None
    models: list[str] = Field(default_factory=list)


class ModelStat(BaseModel):
    model: str
    provider: str
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0
    cost_known: bool = True
    session_count: int = 0


class TimeBucket(BaseModel):
    date: str
    session_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0


class Overview(BaseModel):
    session_count: int = 0
    total_usage: Usage = Field(default_factory=Usage)
    total_cost: float = 0.0
    cost_known: bool = True
    by_model: list[ModelStat] = Field(default_factory=list)
    by_project: list[ProjectSummary] = Field(default_factory=list)
    timeseries: list[TimeBucket] = Field(default_factory=list)
```

- [ ] **Step 4: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_models.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/tests/test_models.py
git commit -m "feat(backend): add Pydantic data models"
```

---

## Task 3: JSONL parser

**Files:**
- Create: `backend/app/parser.py`, `backend/tests/fixtures/sample.jsonl`, `backend/tests/fixtures/corrupt.jsonl`
- Test: `backend/tests/test_parser.py`

**Interfaces:**
- Consumes: `app.models.MessageRecord`, `Usage`.
- Produces:
  - `ParsedSession(session_id: str|None, ai_title: str|None, records: list[MessageRecord], skipped_lines: int)` (Pydantic model, defined in `parser.py`).
  - `parse_session_file(path: Path) -> ParsedSession`.
  - `parse_lines(lines: Iterable[str]) -> ParsedSession` (used by watcher for incremental parsing).

Token mapping from a JSONL assistant line's `message.usage`: `input ← input_tokens`, `output ← output_tokens`, `cache_read ← cache_read_input_tokens`, `cache_write_5m ← cache_creation.ephemeral_5m_input_tokens`, `cache_write_1h ← cache_creation.ephemeral_1h_input_tokens`, `web_search ← server_tool_use.web_search_requests`, `web_fetch ← server_tool_use.web_fetch_requests`. Tools: names of `content` items where `type == "tool_use"`. `content_kinds`: distinct `type` values in `content`. `ai_title` comes from lines where top-level `type == "ai-title"` (field `aiTitle`).

- [ ] **Step 1: Create `backend/tests/fixtures/sample.jsonl`** (one object per line)

```json
{"type":"ai-title","aiTitle":"Fix backup loop","sessionId":"sess-1"}
{"type":"user","uuid":"u1","sessionId":"sess-1","timestamp":"2026-06-11T17:00:00.000Z","cwd":"/home/vemore/workspace/countscore","gitBranch":"main","version":"2.1.173","message":{"role":"user","content":"resume"}}
{"type":"assistant","uuid":"a1","parentUuid":"u1","sessionId":"sess-1","timestamp":"2026-06-11T17:01:27.474Z","gitBranch":"main","version":"2.1.173","message":{"model":"claude-opus-4-8","content":[{"type":"thinking"},{"type":"tool_use","name":"Bash","input":{}}],"usage":{"input_tokens":404,"output_tokens":309,"cache_read_input_tokens":16285,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":9665},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0}}}}
{"type":"assistant","uuid":"a2","parentUuid":"a1","sessionId":"sess-1","timestamp":"2026-06-11T17:02:00.000Z","gitBranch":"main","version":"2.1.173","message":{"model":"claude-opus-4-8","content":[{"type":"text"}],"usage":{"input_tokens":10,"output_tokens":50}}}
```

- [ ] **Step 2: Create `backend/tests/fixtures/corrupt.jsonl`**

```json
{"type":"user","uuid":"u1","sessionId":"sess-2","timestamp":"2026-06-11T17:00:00.000Z","message":{"role":"user","content":"hi"}}
this is not json
{"type":"assistant","uuid":"a1","sessionId":"sess-2","timestamp":"2026-06-11T17:00:05.000Z","message":{"model":"claude-haiku-4-5","content":[{"type":"text"}]}}
```

- [ ] **Step 3: Write the failing test `backend/tests/test_parser.py`**

```python
from pathlib import Path

from app.parser import parse_session_file

FIX = Path(__file__).parent / "fixtures"


def test_parse_sample():
    p = parse_session_file(FIX / "sample.jsonl")
    assert p.session_id == "sess-1"
    assert p.ai_title == "Fix backup loop"
    assert p.skipped_lines == 0
    assistants = [r for r in p.records if r.type == "assistant"]
    assert len(assistants) == 2
    first = assistants[0]
    assert first.model == "claude-opus-4-8"
    assert first.usage.input == 404
    assert first.usage.output == 309
    assert first.usage.cache_read == 16285
    assert first.usage.cache_write_1h == 9665
    assert first.tools == ["Bash"]
    assert set(first.content_kinds) == {"thinking", "tool_use"}


def test_parse_handles_corruption_and_missing_usage():
    p = parse_session_file(FIX / "corrupt.jsonl")
    assert p.skipped_lines == 1  # the "this is not json" line
    a = [r for r in p.records if r.type == "assistant"][0]
    assert a.usage.input == 0  # missing usage -> zeros, no crash
```

- [ ] **Step 4: Run test, expect FAIL** (`ModuleNotFoundError: app.parser`)

Run: `cd backend && uv run pytest tests/test_parser.py -v`

- [ ] **Step 5: Write `backend/app/parser.py`**

```python
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from app.models import MessageRecord, Usage


class ParsedSession(BaseModel):
    session_id: str | None = None
    ai_title: str | None = None
    records: list[MessageRecord] = Field(default_factory=list)
    skipped_lines: int = 0


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _usage_from(message: dict) -> Usage:
    u = message.get("usage") or {}
    cc = u.get("cache_creation") or {}
    st = u.get("server_tool_use") or {}
    return Usage(
        input=u.get("input_tokens", 0) or 0,
        output=u.get("output_tokens", 0) or 0,
        cache_read=u.get("cache_read_input_tokens", 0) or 0,
        cache_write_5m=cc.get("ephemeral_5m_input_tokens", 0) or 0,
        cache_write_1h=cc.get("ephemeral_1h_input_tokens", 0) or 0,
        web_search=st.get("web_search_requests", 0) or 0,
        web_fetch=st.get("web_fetch_requests", 0) or 0,
    )


def _record_from(obj: dict) -> MessageRecord:
    message = obj.get("message") or {}
    content = message.get("content")
    tools: list[str] = []
    kinds: list[str] = []
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            kind = c.get("type")
            if kind:
                kinds.append(kind)
            if kind == "tool_use" and c.get("name"):
                tools.append(c["name"])
    return MessageRecord(
        uuid=obj.get("uuid"),
        parent_uuid=obj.get("parentUuid"),
        timestamp=_parse_ts(obj.get("timestamp")),
        type=obj.get("type", "unknown"),
        model=message.get("model"),
        git_branch=obj.get("gitBranch"),
        cwd=obj.get("cwd"),
        cc_version=obj.get("version"),
        usage=_usage_from(message),
        tools=tools,
        content_kinds=list(dict.fromkeys(kinds)),
    )


def parse_lines(lines: Iterable[str]) -> ParsedSession:
    parsed = ParsedSession()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            parsed.skipped_lines += 1
            continue
        if not isinstance(obj, dict):
            parsed.skipped_lines += 1
            continue
        if parsed.session_id is None and obj.get("sessionId"):
            parsed.session_id = obj["sessionId"]
        if obj.get("type") == "ai-title":
            parsed.ai_title = obj.get("aiTitle")
            continue
        if obj.get("type") in {"user", "assistant", "system"}:
            parsed.records.append(_record_from(obj))
    return parsed


def parse_session_file(path: Path) -> ParsedSession:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return parse_lines(fh)
```

- [ ] **Step 6: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_parser.py -v`

- [ ] **Step 7: Commit**

```bash
git add backend/app/parser.py backend/tests/test_parser.py backend/tests/fixtures
git commit -m "feat(backend): JSONL session parser"
```

---

## Task 4: Pricing

**Files:**
- Create: `backend/app/pricing.py`, `pricing.json` (repo root)
- Test: `backend/tests/test_pricing.py`

**Interfaces:**
- Consumes: `app.models.Usage`.
- Produces:
  - `PriceTable.load(path: Path) -> PriceTable`.
  - `PriceTable.cost_for_usage(usage: Usage, model: str|None, provider: str) -> tuple[float, bool]` — returns `(cost, known)`. `known=False` when the (provider, model) has no entry; cost is `0.0` in that case.
  - `detect_provider(model: str|None, default: str) -> str` — `bedrock` if model starts with `us.anthropic.`/`eu.anthropic.`/contains `bedrock`, else `default`.

- [ ] **Step 1: Create `pricing.json`** (repo root — reference values, user-editable; per **million** tokens)

```json
{
  "anthropic": {
    "claude-opus-4-8":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0,  "cache_read": 0.3},
    "claude-haiku-4-5":  {"input": 1.0, "output": 5.0,  "cache_write_5m": 1.25, "cache_write_1h": 2.0,  "cache_read": 0.1}
  },
  "bedrock": {
    "claude-opus-4-8":   {"input": 5.0, "output": 25.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.5}
  }
}
```

- [ ] **Step 2: Write the failing test `backend/tests/test_pricing.py`**

```python
from pathlib import Path

from app.models import Usage
from app.pricing import PriceTable, detect_provider

PRICING = Path(__file__).resolve().parents[2] / "pricing.json"


def test_cost_known():
    table = PriceTable.load(PRICING)
    u = Usage(input=1_000_000, output=1_000_000, cache_read=1_000_000)
    cost, known = table.cost_for_usage(u, "claude-opus-4-8", "anthropic")
    assert known is True
    assert cost == 5.0 + 25.0 + 0.5


def test_cost_unknown_model_flagged():
    table = PriceTable.load(PRICING)
    cost, known = table.cost_for_usage(Usage(input=100), "made-up-model", "anthropic")
    assert known is False
    assert cost == 0.0


def test_detect_provider():
    assert detect_provider("us.anthropic.claude-opus-4-8-v1:0", "anthropic") == "bedrock"
    assert detect_provider("claude-opus-4-8", "anthropic") == "anthropic"
    assert detect_provider(None, "anthropic") == "anthropic"
```

- [ ] **Step 3: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_pricing.py -v`

- [ ] **Step 4: Write `backend/app/pricing.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

from app.models import Usage

_MILLION = 1_000_000


def detect_provider(model: str | None, default: str) -> str:
    if not model:
        return default
    m = model.lower()
    if m.startswith("us.anthropic.") or m.startswith("eu.anthropic.") or "bedrock" in m:
        return "bedrock"
    return default


class PriceTable:
    def __init__(self, table: dict[str, dict[str, dict[str, float]]]):
        self._table = table

    @classmethod
    def load(cls, path: Path) -> "PriceTable":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def cost_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> tuple[float, bool]:
        prices = self._table.get(provider, {}).get(model or "")
        if prices is None:
            return 0.0, False
        cost = (
            usage.input * prices.get("input", 0.0)
            + usage.output * prices.get("output", 0.0)
            + usage.cache_write_5m * prices.get("cache_write_5m", 0.0)
            + usage.cache_write_1h * prices.get("cache_write_1h", 0.0)
            + usage.cache_read * prices.get("cache_read", 0.0)
        ) / _MILLION
        return cost, True
```

- [ ] **Step 5: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_pricing.py -v`

- [ ] **Step 6: Commit**

```bash
git add backend/app/pricing.py pricing.json backend/tests/test_pricing.py
git commit -m "feat(backend): configurable price table and cost calc"
```

---

## Task 5: Session summary derivation

**Files:**
- Create: `backend/app/summary.py`
- Test: `backend/tests/test_summary.py`

**Interfaces:**
- Consumes: `app.parser.ParsedSession`, `app.pricing.PriceTable`, `detect_provider`, `app.models.SessionSummary`, `Usage`.
- Produces: `summarize_session(parsed: ParsedSession, *, file_path: Path, project: str, table: PriceTable, default_provider: str, active_threshold_seconds: int, now_ts: float, mtime: float) -> SessionSummary`. `is_active = (now_ts - mtime) <= active_threshold_seconds`. Provider is detected from the first assistant model. Per-message cost summed; `cost_known=False` if any assistant message had an unknown (provider, model).

- [ ] **Step 1: Write the failing test `backend/tests/test_summary.py`**

```python
from pathlib import Path

from app.parser import parse_session_file
from app.pricing import PriceTable
from app.summary import summarize_session

FIX = Path(__file__).parent / "fixtures"
PRICING = Path(__file__).resolve().parents[2] / "pricing.json"


def test_summarize_sample():
    parsed = parse_session_file(FIX / "sample.jsonl")
    table = PriceTable.load(PRICING)
    s = summarize_session(
        parsed,
        file_path=FIX / "sample.jsonl",
        project="-home-vemore-workspace-countscore",
        table=table,
        default_provider="anthropic",
        active_threshold_seconds=30,
        now_ts=1_000_000.0,
        mtime=999_990.0,  # 10s ago -> active
    )
    assert s.session_id == "sess-1"
    assert s.ai_title == "Fix backup loop"
    assert s.message_count == 3  # 1 user + 2 assistant records
    assert s.models == ["claude-opus-4-8"]
    assert s.provider == "anthropic"
    assert s.usage.input == 414  # 404 + 10
    assert s.tool_counts == {"Bash": 1}
    assert s.is_active is True
    assert s.cost_known is True
    assert s.cost > 0


def test_unknown_model_sets_cost_known_false():
    parsed = parse_session_file(FIX / "corrupt.jsonl")
    table = PriceTable.load(PRICING)  # haiku exists, so make it unknown by empty table
    empty = PriceTable({})
    s = summarize_session(
        parsed, file_path=FIX / "corrupt.jsonl", project="p",
        table=empty, default_provider="anthropic",
        active_threshold_seconds=30, now_ts=2_000_000.0, mtime=0.0,
    )
    assert s.cost_known is False
    assert s.is_active is False
```

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_summary.py -v`

- [ ] **Step 3: Write `backend/app/summary.py`**

```python
from __future__ import annotations

from pathlib import Path

from app.models import SessionSummary, Usage
from app.parser import ParsedSession
from app.pricing import PriceTable, detect_provider


def summarize_session(
    parsed: ParsedSession,
    *,
    file_path: Path,
    project: str,
    table: PriceTable,
    default_provider: str,
    active_threshold_seconds: int,
    now_ts: float,
    mtime: float,
) -> SessionSummary:
    total = Usage()
    tool_counts: dict[str, int] = {}
    models: list[str] = []
    timestamps = []
    cost = 0.0
    cost_known = True
    provider = default_provider
    git_branch = None
    cc_version = None
    cwd = None

    for r in parsed.records:
        if r.timestamp:
            timestamps.append(r.timestamp)
        git_branch = git_branch or r.git_branch
        cc_version = cc_version or r.cc_version
        cwd = cwd or r.cwd
        for t in r.tools:
            tool_counts[t] = tool_counts.get(t, 0) + 1
        if r.type == "assistant" and r.model:
            if r.model not in models:
                models.append(r.model)
            provider = detect_provider(r.model, default_provider)
            total = total.add(r.usage)
            c, known = table.cost_for_usage(r.usage, r.model, provider)
            cost += c
            cost_known = cost_known and known

    started = min(timestamps) if timestamps else None
    ended = max(timestamps) if timestamps else None
    duration = (ended - started).total_seconds() if started and ended else None

    return SessionSummary(
        session_id=parsed.session_id or file_path.stem,
        project=project,
        cwd=cwd,
        file_path=str(file_path),
        ai_title=parsed.ai_title,
        started_at=started,
        ended_at=ended,
        duration_seconds=duration,
        is_active=(now_ts - mtime) <= active_threshold_seconds,
        models=models,
        provider=provider,
        git_branch=git_branch,
        cc_version=cc_version,
        message_count=len(parsed.records),
        usage=total,
        cost=cost,
        cost_known=cost_known,
        tool_counts=tool_counts,
        skipped_lines=parsed.skipped_lines,
    )
```

- [ ] **Step 4: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_summary.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/summary.py backend/tests/test_summary.py
git commit -m "feat(backend): session summary derivation"
```

---

## Task 6: Store (mtime-keyed cache)

**Files:**
- Create: `backend/app/store.py`
- Test: `backend/tests/test_store.py`

**Interfaces:**
- Consumes: `app.config.Settings`, `app.pricing.PriceTable`, `app.parser.parse_session_file`, `app.summary.summarize_session`, `app.models.SessionSummary`.
- Produces:
  - `SessionStore(settings: Settings)` with:
    - `get_summary(file_path: Path) -> SessionSummary` (caches by `(path, mtime)`; reparses only when mtime changes).
    - `all_summaries() -> list[SessionSummary]` (scans `settings.projects_dir/*/*.jsonl`).
    - `project_name_for(file_path: Path) -> str` (the parent dir name).
    - `reload_pricing() -> None`.
  - Uses `time.time()` for `now_ts` and `path.stat().st_mtime` for `mtime`.

- [ ] **Step 1: Write the failing test `backend/tests/test_store.py`**

```python
import shutil
from pathlib import Path

from app.config import Settings
from app.store import SessionStore

FIX = Path(__file__).parent / "fixtures"


def _make_settings(tmp_path) -> Settings:
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "sample.jsonl", projects / "sess-1.jsonl")
    return Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
    )


def test_all_summaries(tmp_path):
    store = SessionStore(_make_settings(tmp_path))
    summaries = store.all_summaries()
    assert len(summaries) == 1
    assert summaries[0].session_id == "sess-1"
    assert summaries[0].project == "-home-vemore-workspace-countscore"


def test_cache_reuses_until_mtime_changes(tmp_path, monkeypatch):
    settings = _make_settings(tmp_path)
    store = SessionStore(settings)
    f = next((settings.projects_dir).rglob("*.jsonl"))

    calls = {"n": 0}
    import app.store as store_mod
    real = store_mod.parse_session_file

    def counting_parse(path):
        calls["n"] += 1
        return real(path)

    monkeypatch.setattr(store_mod, "parse_session_file", counting_parse)
    store.get_summary(f)
    store.get_summary(f)
    assert calls["n"] == 1  # second call served from cache
```

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_store.py -v`

- [ ] **Step 3: Write `backend/app/store.py`**

```python
from __future__ import annotations

import time
from pathlib import Path

from app.config import Settings
from app.models import SessionSummary
from app.parser import parse_session_file
from app.pricing import PriceTable
from app.summary import summarize_session


class SessionStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._table = PriceTable.load(settings.pricing_path)
        self._cache: dict[str, tuple[float, SessionSummary]] = {}

    def reload_pricing(self) -> None:
        self._table = PriceTable.load(self._settings.pricing_path)
        self._cache.clear()

    def project_name_for(self, file_path: Path) -> str:
        return file_path.parent.name

    def get_summary(self, file_path: Path) -> SessionSummary:
        mtime = file_path.stat().st_mtime
        key = str(file_path)
        cached = self._cache.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
        parsed = parse_session_file(file_path)
        summary = summarize_session(
            parsed,
            file_path=file_path,
            project=self.project_name_for(file_path),
            table=self._table,
            default_provider=self._settings.default_provider,
            active_threshold_seconds=self._settings.live_active_threshold_seconds,
            now_ts=time.time(),
            mtime=mtime,
        )
        self._cache[key] = (mtime, summary)
        return summary

    def all_summaries(self) -> list[SessionSummary]:
        root = self._settings.projects_dir
        if not root.exists():
            return []
        summaries: list[SessionSummary] = []
        for path in sorted(root.glob("*/*.jsonl")):
            try:
                summaries.append(self.get_summary(path))
            except OSError:
                continue
        return summaries
```

- [ ] **Step 4: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_store.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/store.py backend/tests/test_store.py
git commit -m "feat(backend): mtime-keyed session store cache"
```

---

## Task 7: Metrics aggregation

**Files:**
- Create: `backend/app/metrics.py`
- Test: `backend/tests/test_metrics.py`

**Interfaces:**
- Consumes: `app.models.{SessionSummary, ProjectSummary, ModelStat, TimeBucket, Overview, Usage}`.
- Produces (all take `summaries: list[SessionSummary]`):
  - `build_overview(summaries) -> Overview` — totals, `by_model` (ModelStat per model), `by_project` (ProjectSummary list), `timeseries` (TimeBucket per day from `started_at`). `cost_known` is the AND of all summaries.
  - `list_projects(summaries) -> list[ProjectSummary]`.
  - `project_detail(summaries, project: str) -> tuple[ProjectSummary, list[SessionSummary]]` — the project aggregate plus its sessions sorted by `last activity` desc. Raises `KeyError` if no sessions for that project.

- [ ] **Step 1: Write the failing test `backend/tests/test_metrics.py`**

```python
from datetime import datetime, timezone

from app.models import SessionSummary, Usage
from app.metrics import build_overview, list_projects, project_detail


def _s(session_id, project, model, inp, out, day) -> SessionSummary:
    ts = datetime(2026, 6, day, 12, 0, tzinfo=timezone.utc)
    return SessionSummary(
        session_id=session_id, project=project, file_path=f"/x/{session_id}.jsonl",
        started_at=ts, ended_at=ts, models=[model], provider="anthropic",
        message_count=2, usage=Usage(input=inp, output=out), cost=1.0, cost_known=True,
    )


def test_build_overview():
    summaries = [
        _s("a", "proj1", "claude-opus-4-8", 100, 10, 11),
        _s("b", "proj1", "claude-opus-4-8", 200, 20, 12),
        _s("c", "proj2", "claude-haiku-4-5", 50, 5, 12),
    ]
    ov = build_overview(summaries)
    assert ov.session_count == 3
    assert ov.total_usage.input == 350
    assert ov.total_cost == 3.0
    models = {m.model: m for m in ov.by_model}
    assert models["claude-opus-4-8"].usage.input == 300
    assert models["claude-opus-4-8"].session_count == 2
    projects = {p.name: p for p in ov.by_project}
    assert projects["proj1"].session_count == 2
    days = {b.date: b for b in ov.timeseries}
    assert days["2026-06-12"].session_count == 2


def test_project_detail():
    summaries = [_s("a", "proj1", "claude-opus-4-8", 100, 10, 11)]
    agg, sessions = project_detail(summaries, "proj1")
    assert agg.session_count == 1
    assert len(sessions) == 1
```

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_metrics.py -v`

- [ ] **Step 3: Write `backend/app/metrics.py`**

```python
from __future__ import annotations

from app.models import (
    ModelStat,
    Overview,
    ProjectSummary,
    SessionSummary,
    TimeBucket,
    Usage,
)


def _merge_models(existing: list[str], new: list[str]) -> list[str]:
    out = list(existing)
    for m in new:
        if m not in out:
            out.append(m)
    return out


def list_projects(summaries: list[SessionSummary]) -> list[ProjectSummary]:
    acc: dict[str, ProjectSummary] = {}
    for s in summaries:
        p = acc.get(s.project)
        if p is None:
            p = ProjectSummary(name=s.project, path=s.cwd or s.project)
            acc[s.project] = p
        p.session_count += 1
        p.usage = p.usage.add(s.usage)
        p.cost += s.cost
        p.cost_known = p.cost_known and s.cost_known
        p.models = _merge_models(p.models, s.models)
        last = s.ended_at or s.started_at
        if last and (p.last_activity is None or last > p.last_activity):
            p.last_activity = last
    return sorted(
        acc.values(),
        key=lambda x: x.last_activity or x.name,  # type: ignore[return-value]
        reverse=True,
    )


def build_overview(summaries: list[SessionSummary]) -> Overview:
    total = Usage()
    total_cost = 0.0
    cost_known = True
    model_acc: dict[str, ModelStat] = {}
    day_acc: dict[str, TimeBucket] = {}

    for s in summaries:
        total = total.add(s.usage)
        total_cost += s.cost
        cost_known = cost_known and s.cost_known

        model_key = s.models[0] if s.models else "(none)"
        ms = model_acc.get(model_key)
        if ms is None:
            ms = ModelStat(model=model_key, provider=s.provider)
            model_acc[model_key] = ms
        ms.usage = ms.usage.add(s.usage)
        ms.cost += s.cost
        ms.cost_known = ms.cost_known and s.cost_known
        ms.session_count += 1

        day = (s.started_at or s.ended_at)
        if day:
            key = day.date().isoformat()
            tb = day_acc.get(key)
            if tb is None:
                tb = TimeBucket(date=key)
                day_acc[key] = tb
            tb.session_count += 1
            tb.usage = tb.usage.add(s.usage)
            tb.cost += s.cost

    return Overview(
        session_count=len(summaries),
        total_usage=total,
        total_cost=total_cost,
        cost_known=cost_known,
        by_model=sorted(model_acc.values(), key=lambda m: m.cost, reverse=True),
        by_project=list_projects(summaries),
        timeseries=sorted(day_acc.values(), key=lambda b: b.date),
    )


def project_detail(
    summaries: list[SessionSummary], project: str
) -> tuple[ProjectSummary, list[SessionSummary]]:
    sessions = [s for s in summaries if s.project == project]
    if not sessions:
        raise KeyError(project)
    agg = list_projects(sessions)[0]
    sessions = sorted(
        sessions,
        key=lambda s: s.ended_at or s.started_at or s.session_id,
        reverse=True,
    )
    return agg, sessions
```

- [ ] **Step 4: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_metrics.py -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/metrics.py backend/tests/test_metrics.py
git commit -m "feat(backend): metrics aggregation"
```

---

## Task 8: FastAPI REST endpoints

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `app.config.get_settings`, `app.store.SessionStore`, `app.metrics.*`, `app.parser.parse_session_file`.
- Produces FastAPI app `app` with routes:
  - `GET /api/overview` → `Overview`.
  - `GET /api/projects` → `list[ProjectSummary]`.
  - `GET /api/projects/{project}` → `{"project": ProjectSummary, "sessions": list[SessionSummary]}` (404 if unknown).
  - `GET /api/sessions/{session_id}` → `{"summary": SessionSummary, "messages": list[MessageRecord]}` (404 if not found). Finds the file by scanning summaries for matching `session_id`.
  - `GET /api/health` → `{"status": "ok"}`.
  - A module-level `get_store()` dependency returns a singleton `SessionStore`.

- [ ] **Step 1: Write the failing test `backend/tests/test_api.py`**

```python
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, get_store
from app.store import SessionStore

FIX = Path(__file__).parent / "fixtures"


def _client(tmp_path):
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "sample.jsonl", projects / "sess-1.jsonl")
    settings = Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
    )
    app.dependency_overrides[get_store] = lambda: SessionStore(settings)
    return TestClient(app)


def test_overview(tmp_path):
    client = _client(tmp_path)
    r = client.get("/api/overview")
    assert r.status_code == 200
    assert r.json()["session_count"] == 1


def test_session_detail(tmp_path):
    client = _client(tmp_path)
    r = client.get("/api/sessions/sess-1")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["session_id"] == "sess-1"
    assert len(body["messages"]) == 3


def test_session_404(tmp_path):
    client = _client(tmp_path)
    assert client.get("/api/sessions/nope").status_code == 404
```

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_api.py -v`

- [ ] **Step 3: Write `backend/app/main.py`**

```python
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.metrics import build_overview, list_projects, project_detail
from app.parser import parse_session_file
from app.store import SessionStore

app = FastAPI(title="CCDashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_store() -> SessionStore:
    return SessionStore(get_settings())


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/overview")
def overview(store: SessionStore = Depends(get_store)):
    return build_overview(store.all_summaries())


@app.get("/api/projects")
def projects(store: SessionStore = Depends(get_store)):
    return list_projects(store.all_summaries())


@app.get("/api/projects/{project}")
def project(project: str, store: SessionStore = Depends(get_store)):
    try:
        agg, sessions = project_detail(store.all_summaries(), project)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found")
    return {"project": agg, "sessions": sessions}


@app.get("/api/sessions/{session_id}")
def session(session_id: str, store: SessionStore = Depends(get_store)):
    for summary in store.all_summaries():
        if summary.session_id == session_id:
            parsed = parse_session_file(Path(summary.file_path))
            return {"summary": summary, "messages": parsed.records}
    raise HTTPException(status_code=404, detail="session not found")
```

- [ ] **Step 4: Run test, expect PASS**

Run: `cd backend && uv run pytest tests/test_api.py -v`

- [ ] **Step 5: Manual smoke check**

Run: `cd backend && uv run uvicorn app.main:app --port 8787 &` then `curl -s localhost:8787/api/health`
Expected: `{"status":"ok"}`. Stop the server afterward (`kill %1`).

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/tests/test_api.py
git commit -m "feat(backend): REST endpoints"
```

---

## Task 9: Live watcher + SSE endpoint

**Files:**
- Modify: `backend/app/main.py` (add `/api/live` SSE route + `live_state` wiring)
- Create: `backend/app/watcher.py`
- Test: `backend/tests/test_watcher.py`

**Interfaces:**
- Consumes: `app.store.SessionStore`.
- Produces:
  - `active_sessions(store: SessionStore) -> list[SessionSummary]` — summaries where `is_active` is True.
  - `live_snapshot(store: SessionStore) -> dict` — `{"active": [SessionSummary...], "generated_at": iso}` serializable payload for one SSE tick.
  - In `main.py`: `GET /api/live` → `text/event-stream` that emits `live_snapshot` every ~2s using `sse-starlette`'s `EventSourceResponse` (add dep `sse-starlette>=2.0` in Task 1's pyproject — see note). Each event is `data: <json>\n\n`.

> Note: add `sse-starlette>=2.0` to `backend/pyproject.toml` dependencies as part of Step 1 here, then `uv sync`.

- [ ] **Step 1: Add dependency**

Edit `backend/pyproject.toml` dependencies to include `"sse-starlette>=2.0"`, then run `cd backend && uv sync`.

- [ ] **Step 2: Write the failing test `backend/tests/test_watcher.py`**

```python
import shutil
import time
from pathlib import Path

from app.config import Settings
from app.store import SessionStore
from app.watcher import active_sessions, live_snapshot

FIX = Path(__file__).parent / "fixtures"


def _store(tmp_path) -> SessionStore:
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    dest = projects / "sess-1.jsonl"
    shutil.copy(FIX / "sample.jsonl", dest)
    now = time.time()
    import os
    os.utime(dest, (now, now))  # fresh mtime -> active
    settings = Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
        live_active_threshold_seconds=3600,
    )
    return SessionStore(settings)


def test_active_sessions(tmp_path):
    store = _store(tmp_path)
    active = active_sessions(store)
    assert len(active) == 1
    assert active[0].is_active is True


def test_live_snapshot_shape(tmp_path):
    snap = live_snapshot(_store(tmp_path))
    assert "active" in snap
    assert "generated_at" in snap
    assert len(snap["active"]) == 1
```

- [ ] **Step 3: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_watcher.py -v`

- [ ] **Step 4: Write `backend/app/watcher.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone

from app.models import SessionSummary
from app.store import SessionStore


def active_sessions(store: SessionStore) -> list[SessionSummary]:
    return [s for s in store.all_summaries() if s.is_active]


def live_snapshot(store: SessionStore) -> dict:
    active = active_sessions(store)
    return {
        "active": [s.model_dump(mode="json") for s in active],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 5: Add SSE route to `backend/app/main.py`**

Add imports near the top:

```python
import asyncio
import json

from sse_starlette.sse import EventSourceResponse

from app.watcher import live_snapshot
```

Add route at the end of `main.py`:

```python
@app.get("/api/live")
async def live(store: SessionStore = Depends(get_store)):
    async def event_generator():
        while True:
            yield {"data": json.dumps(live_snapshot(store))}
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
```

- [ ] **Step 6: Run watcher tests, expect PASS**

Run: `cd backend && uv run pytest tests/test_watcher.py -v`

- [ ] **Step 7: Run full backend suite, expect all PASS**

Run: `cd backend && uv run pytest -v`

- [ ] **Step 8: Commit**

```bash
git add backend/app/watcher.py backend/app/main.py backend/pyproject.toml backend/uv.lock backend/tests/test_watcher.py
git commit -m "feat(backend): live watcher and SSE endpoint"
```

---

## Task 10: Exporter

**Files:**
- Create: `backend/app/exporter.py`
- Modify: `backend/app/main.py` (start periodic export task on startup if enabled)
- Test: `backend/tests/test_exporter.py`

**Interfaces:**
- Consumes: `app.config.Settings`, `app.store.SessionStore`, `app.metrics.list_projects`, `app.models.{SessionSummary, ProjectSummary}`.
- Produces:
  - `build_payload(summaries, projects, settings, sent_at: str) -> dict` — `schema_version=1`, `source={machine_id,user_id,instance_id}`, `sent_at`, `sessions`, `projects`. Each session is aggregates-only; enriched fields `ai_title`/`git_branch`/`cc_version` are stripped to `None` unless `settings.export_include_enriched`.
  - `Exporter(settings, store)` with:
    - `_cursor: dict[str, str]` mapping `session_id → last exported ended_at iso`.
    - `pending(summaries) -> list[SessionSummary]` — sessions whose `ended_at` iso differs from cursor.
    - `async send_once(client: httpx.AsyncClient) -> bool` — builds payload from pending, POSTs to `settings.export_endpoint` with bearer token; on 2xx advances cursor and returns True; else returns False (cursor unchanged).
    - `async run_periodic()` — loop sleeping `interval_minutes`; only active when `settings.export_enabled`.

- [ ] **Step 1: Write the failing test `backend/tests/test_exporter.py`**

```python
from datetime import datetime, timezone

import httpx
import pytest

from app.config import Settings
from app.exporter import Exporter, build_payload
from app.models import ProjectSummary, SessionSummary, Usage


def _summary(sid, enriched_title="secret") -> SessionSummary:
    ts = datetime(2026, 6, 12, tzinfo=timezone.utc)
    return SessionSummary(
        session_id=sid, project="p", file_path=f"/x/{sid}.jsonl",
        ai_title=enriched_title, git_branch="main", cc_version="2.1",
        started_at=ts, ended_at=ts, models=["claude-opus-4-8"], provider="anthropic",
        message_count=2, usage=Usage(input=10, output=5), cost=1.0, cost_known=True,
    )


def test_payload_strips_enriched_by_default():
    s = _summary("a")
    p = ProjectSummary(name="p", path="/x")
    settings = Settings(export_include_enriched=False)
    payload = build_payload([s], [p], settings, sent_at="2026-06-28T00:00:00Z")
    assert payload["schema_version"] == 1
    sess = payload["sessions"][0]
    assert sess["ai_title"] is None
    assert sess["git_branch"] is None
    assert sess["usage"]["input"] == 10  # aggregates kept


def test_payload_keeps_enriched_when_enabled():
    settings = Settings(export_include_enriched=True)
    payload = build_payload([_summary("a")], [], settings, sent_at="t")
    assert payload["sessions"][0]["ai_title"] == "secret"


@pytest.mark.asyncio
async def test_send_once_advances_cursor_on_success():
    settings = Settings(export_enabled=True, export_endpoint="http://mock/ingest",
                        export_token="tok")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = request.content
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)

    class FakeStore:
        def all_summaries(self_inner):
            return [_summary("a")]

    exporter = Exporter(settings, FakeStore())
    async with httpx.AsyncClient(transport=transport) as client:
        ok = await exporter.send_once(client)
    assert ok is True
    assert captured["auth"] == "Bearer tok"
    # second send: nothing pending -> still True, no new data
    async with httpx.AsyncClient(transport=transport) as client:
        assert exporter.pending(FakeStore().all_summaries()) == []
```

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd backend && uv run pytest tests/test_exporter.py -v`

- [ ] **Step 3: Write `backend/app/exporter.py`**

```python
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.metrics import list_projects
from app.models import ProjectSummary, SessionSummary

ENRICHED_FIELDS = ("ai_title", "git_branch", "cc_version")


def _session_payload(s: SessionSummary, include_enriched: bool) -> dict:
    data = s.model_dump(mode="json")
    if not include_enriched:
        for field in ENRICHED_FIELDS:
            data[field] = None
    return data


def build_payload(
    summaries: list[SessionSummary],
    projects: list[ProjectSummary],
    settings: Settings,
    sent_at: str,
) -> dict:
    return {
        "schema_version": 1,
        "source": {
            "machine_id": settings.export_machine_id,
            "user_id": settings.export_user_id,
            "instance_id": settings.export_instance_id,
        },
        "sent_at": sent_at,
        "sessions": [
            _session_payload(s, settings.export_include_enriched) for s in summaries
        ],
        "projects": [p.model_dump(mode="json") for p in projects],
    }


class Exporter:
    def __init__(self, settings: Settings, store):
        self._settings = settings
        self._store = store
        self._cursor: dict[str, str] = {}

    def _key(self, s: SessionSummary) -> str:
        return (s.ended_at or s.started_at).isoformat() if (s.ended_at or s.started_at) else ""

    def pending(self, summaries: list[SessionSummary]) -> list[SessionSummary]:
        out = []
        for s in summaries:
            if self._cursor.get(s.session_id) != self._key(s):
                out.append(s)
        return out

    async def send_once(self, client: httpx.AsyncClient) -> bool:
        summaries = self._store.all_summaries()
        pending = self.pending(summaries)
        if not pending:
            return True
        payload = build_payload(
            pending,
            list_projects(summaries),
            self._settings,
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        headers = {"Authorization": f"Bearer {self._settings.export_token}"}
        try:
            resp = await client.post(
                self._settings.export_endpoint, json=payload, headers=headers, timeout=30
            )
        except httpx.HTTPError:
            return False
        if resp.status_code // 100 != 2:
            return False
        for s in pending:
            self._cursor[s.session_id] = self._key(s)
        return True

    async def run_periodic(self) -> None:
        if not self._settings.export_enabled or not self._settings.export_endpoint:
            return
        async with httpx.AsyncClient() as client:
            while True:
                await self.send_once(client)
                await asyncio.sleep(self._settings.export_interval_minutes * 60)
```

- [ ] **Step 4: Wire periodic task into `backend/app/main.py`**

Add near the imports:

```python
from app.exporter import Exporter
```

Add a startup hook at the end of `main.py`:

```python
@app.on_event("startup")
async def _start_exporter():
    settings = get_settings()
    if settings.export_enabled and settings.export_endpoint:
        exporter = Exporter(settings, get_store())
        asyncio.create_task(exporter.run_periodic())
```

- [ ] **Step 5: Run exporter tests, expect PASS**

Run: `cd backend && uv run pytest tests/test_exporter.py -v`

- [ ] **Step 6: Run full backend suite, expect all PASS**

Run: `cd backend && uv run pytest -v`

- [ ] **Step 7: Commit**

```bash
git add backend/app/exporter.py backend/app/main.py backend/tests/test_exporter.py
git commit -m "feat(backend): optional periodic exporter"
```

---

## Task 11: Frontend scaffolding

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/lib/format.ts`
- Test: `frontend/src/test/format.test.ts`

**Interfaces:**
- Produces:
  - `api/client.ts`: typed fetchers `getOverview()`, `getProjects()`, `getProject(name)`, `getSession(id)` against `import.meta.env.VITE_API_BASE ?? "http://localhost:8000"`; plus TS interfaces mirroring backend models (`Usage`, `SessionSummary`, `ProjectSummary`, `Overview`, `MessageRecord`).
  - `lib/format.ts`: `formatTokens(n: number): string`, `formatCost(n: number, currency: string, known: boolean): string` (returns `"—"` / `"n/a"` when `known` is false), `formatDuration(seconds: number|null): string`.
  - `App.tsx`: React Router routes for `/`, `/projects`, `/projects/:name`, `/sessions/:id`, `/live` with a nav layout.

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "ccdashboard-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.40.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "jsdom": "^24.1.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create config files**

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"]
}
```

`frontend/vite.config.ts`:

```typescript
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: [],
  },
});
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CCDashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Create `frontend/src/lib/format.ts`**

```typescript
export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function formatCost(n: number, currency: string, known: boolean): string {
  if (!known) return "n/a";
  return `${n.toFixed(2)} ${currency}`;
}

export function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m >= 60) return `${Math.floor(m / 60)}h${m % 60}m`;
  return `${m}m${s}s`;
}
```

- [ ] **Step 4: Write the failing test `frontend/src/test/format.test.ts`**

```typescript
import { describe, expect, it } from "vitest";

import { formatCost, formatDuration, formatTokens } from "../lib/format";

describe("format", () => {
  it("formats tokens", () => {
    expect(formatTokens(500)).toBe("500");
    expect(formatTokens(1500)).toBe("1.5k");
    expect(formatTokens(2_000_000)).toBe("2.00M");
  });

  it("formats cost with unknown flag", () => {
    expect(formatCost(1.5, "€", true)).toBe("1.50 €");
    expect(formatCost(1.5, "€", false)).toBe("n/a");
  });

  it("formats duration", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(125)).toBe("2m5s");
  });
});
```

- [ ] **Step 5: Install deps and run test, expect PASS**

Run: `cd frontend && npm install && npm test`
Expected: format tests pass.

- [ ] **Step 6: Create `frontend/src/api/client.ts`**

```typescript
const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Usage {
  input: number; output: number;
  cache_write_5m: number; cache_write_1h: number; cache_read: number;
  web_search: number; web_fetch: number;
}
export interface SessionSummary {
  session_id: string; project: string; cwd: string | null; file_path: string;
  ai_title: string | null; started_at: string | null; ended_at: string | null;
  duration_seconds: number | null; is_active: boolean; models: string[];
  provider: string; git_branch: string | null; cc_version: string | null;
  message_count: number; usage: Usage; cost: number; cost_known: boolean;
  tool_counts: Record<string, number>; skipped_lines: number;
}
export interface ProjectSummary {
  name: string; path: string; session_count: number; usage: Usage;
  cost: number; cost_known: boolean; last_activity: string | null; models: string[];
}
export interface ModelStat {
  model: string; provider: string; usage: Usage; cost: number;
  cost_known: boolean; session_count: number;
}
export interface TimeBucket {
  date: string; session_count: number; usage: Usage; cost: number;
}
export interface Overview {
  session_count: number; total_usage: Usage; total_cost: number;
  cost_known: boolean; by_model: ModelStat[]; by_project: ProjectSummary[];
  timeseries: TimeBucket[];
}
export interface MessageRecord {
  uuid: string | null; parent_uuid: string | null; timestamp: string | null;
  type: string; model: string | null; git_branch: string | null;
  cwd: string | null; cc_version: string | null; usage: Usage;
  tools: string[]; content_kinds: string[];
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

export const getOverview = () => get<Overview>("/api/overview");
export const getProjects = () => get<ProjectSummary[]>("/api/projects");
export const getProject = (name: string) =>
  get<{ project: ProjectSummary; sessions: SessionSummary[] }>(
    `/api/projects/${encodeURIComponent(name)}`,
  );
export const getSession = (id: string) =>
  get<{ summary: SessionSummary; messages: MessageRecord[] }>(
    `/api/sessions/${encodeURIComponent(id)}`,
  );
```

- [ ] **Step 7: Create `frontend/src/App.tsx`**

```tsx
import { NavLink, Route, Routes } from "react-router-dom";

import Live from "./pages/Live";
import Overview from "./pages/Overview";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import Session from "./pages/Session";

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 1100, margin: "0 auto", padding: 16 }}>
      <h1>CCDashboard</h1>
      <nav style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <NavLink to="/">Overview</NavLink>
        <NavLink to="/projects">Projects</NavLink>
        <NavLink to="/live">Live</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:name" element={<ProjectDetail />} />
        <Route path="/sessions/:id" element={<Session />} />
        <Route path="/live" element={<Live />} />
      </Routes>
    </div>
  );
}
```

- [ ] **Step 8: Create `frontend/src/main.tsx`**

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

> Note: pages are created in Tasks 12–15. To compile now, create placeholder files for each page exporting `export default function X() { return null; }` so `App.tsx` resolves, then flesh them out in their tasks.

- [ ] **Step 9: Create placeholder pages**

Create `frontend/src/pages/Overview.tsx`, `Projects.tsx`, `ProjectDetail.tsx`, `Session.tsx`, `Live.tsx`, each with:

```tsx
export default function Page() {
  return null;
}
```

- [ ] **Step 10: Verify build & test**

Run: `cd frontend && npm run build && npm test`
Expected: build succeeds, format tests pass.

- [ ] **Step 11: Commit**

```bash
git add frontend
git commit -m "feat(frontend): scaffold Vite/React app, api client, formatters"
```

---

## Task 12: Overview page + KPI/Chart components

**Files:**
- Create: `frontend/src/components/KpiCard.tsx`, `frontend/src/components/UnknownCostBadge.tsx`, `frontend/src/components/CostTokenChart.tsx`
- Modify: `frontend/src/pages/Overview.tsx`
- Test: `frontend/src/test/KpiCard.test.tsx`

**Interfaces:**
- Consumes: `api/client.getOverview`, `lib/format`, `Overview`/`TimeBucket` types.
- Produces:
  - `KpiCard({ label, value }: { label: string; value: string })`.
  - `UnknownCostBadge({ known }: { known: boolean })` — renders a warning chip when `!known`, else nothing.
  - `CostTokenChart({ data }: { data: TimeBucket[] })` — Recharts line/bar of cost & token totals per day.
  - `Overview` page: fetches overview via React Query, shows KPI cards (sessions, total tokens, total cost + badge), `CostTokenChart`, and a top-projects table linking to `/projects/:name`.

- [ ] **Step 1: Write the failing test `frontend/src/test/KpiCard.test.tsx`**

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import KpiCard from "../components/KpiCard";
import UnknownCostBadge from "../components/UnknownCostBadge";

describe("KpiCard", () => {
  it("renders label and value", () => {
    render(<KpiCard label="Sessions" value="42" />);
    expect(screen.getByText("Sessions")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("badge appears only when cost unknown", () => {
    const { container, rerender } = render(<UnknownCostBadge known={true} />);
    expect(container).toBeEmptyDOMElement();
    rerender(<UnknownCostBadge known={false} />);
    expect(screen.getByText(/coût incomplet/i)).toBeInTheDocument();
  });
});
```

Create `frontend/src/test/setup.ts` with `import "@testing-library/jest-dom";` and add it to `vite.config.ts` `test.setupFiles: ["src/test/setup.ts"]`.

- [ ] **Step 2: Run test, expect FAIL**

Run: `cd frontend && npm test`

- [ ] **Step 3: Write `frontend/src/components/KpiCard.tsx`**

```tsx
export default function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, minWidth: 160 }}>
      <div style={{ color: "#666", fontSize: 13 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
```

- [ ] **Step 4: Write `frontend/src/components/UnknownCostBadge.tsx`**

```tsx
export default function UnknownCostBadge({ known }: { known: boolean }) {
  if (known) return null;
  return (
    <span
      title="Un modèle sans tarif a été rencontré"
      style={{ background: "#fde68a", color: "#92400e", borderRadius: 6, padding: "2px 8px", fontSize: 12 }}
    >
      coût incomplet
    </span>
  );
}
```

- [ ] **Step 5: Write `frontend/src/components/CostTokenChart.tsx`**

```tsx
import {
  Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

import type { TimeBucket } from "../api/client";

export default function CostTokenChart({ data }: { data: TimeBucket[] }) {
  const rows = data.map((b) => ({
    date: b.date,
    cost: Number(b.cost.toFixed(2)),
    tokens: b.usage.input + b.usage.output,
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={rows}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip />
        <Legend />
        <Bar yAxisId="left" dataKey="tokens" name="Tokens" fill="#93c5fd" />
        <Line yAxisId="right" dataKey="cost" name="Coût" stroke="#ef4444" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 6: Write `frontend/src/pages/Overview.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getOverview } from "../api/client";
import CostTokenChart from "../components/CostTokenChart";
import KpiCard from "../components/KpiCard";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatTokens } from "../lib/format";

const CURRENCY = "€";

export default function Overview() {
  const { data, isLoading, error } = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Erreur de chargement.</p>;

  const totalTokens = data.total_usage.input + data.total_usage.output;
  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <KpiCard label="Sessions" value={String(data.session_count)} />
        <KpiCard label="Tokens (in+out)" value={formatTokens(totalTokens)} />
        <KpiCard label="Coût total" value={formatCost(data.total_cost, CURRENCY, data.cost_known)} />
      </div>
      <div style={{ margin: "8px 0" }}>
        <UnknownCostBadge known={data.cost_known} />
      </div>
      <h2>Activité & coût par jour</h2>
      <CostTokenChart data={data.timeseries} />
      <h2>Top projets</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th></tr>
        </thead>
        <tbody>
          {data.by_project.map((p) => (
            <tr key={p.name}>
              <td><Link to={`/projects/${encodeURIComponent(p.name)}`}>{p.name}</Link></td>
              <td align="center">{p.session_count}</td>
              <td align="center">{formatTokens(p.usage.input + p.usage.output)}</td>
              <td align="center">{formatCost(p.cost, CURRENCY, p.cost_known)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 7: Run test + build, expect PASS**

Run: `cd frontend && npm test && npm run build`

- [ ] **Step 8: Commit**

```bash
git add frontend/src
git commit -m "feat(frontend): overview page with KPIs and chart"
```

---

## Task 13: Projects + ProjectDetail pages

**Files:**
- Modify: `frontend/src/pages/Projects.tsx`, `frontend/src/pages/ProjectDetail.tsx`

**Interfaces:**
- Consumes: `api/client.getProjects`, `getProject`, `lib/format`.
- Produces: Projects list page (table linking to detail); ProjectDetail page showing the project aggregate KPIs and its sessions table, each session linking to `/sessions/:id`.

- [ ] **Step 1: Write `frontend/src/pages/Projects.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getProjects } from "../api/client";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatTokens } from "../lib/format";

export default function Projects() {
  const { data, isLoading, error } = useQuery({ queryKey: ["projects"], queryFn: getProjects });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Erreur de chargement.</p>;
  return (
    <div>
      <h2>Projets</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th><th>Dernière activité</th></tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.name}>
              <td>
                <Link to={`/projects/${encodeURIComponent(p.name)}`}>{p.name}</Link>{" "}
                <UnknownCostBadge known={p.cost_known} />
              </td>
              <td align="center">{p.session_count}</td>
              <td align="center">{formatTokens(p.usage.input + p.usage.output)}</td>
              <td align="center">{formatCost(p.cost, "€", p.cost_known)}</td>
              <td align="center">{p.last_activity?.slice(0, 10) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/src/pages/ProjectDetail.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getProject } from "../api/client";
import KpiCard from "../components/KpiCard";
import { formatCost, formatDuration, formatTokens } from "../lib/format";

export default function ProjectDetail() {
  const { name = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", name],
    queryFn: () => getProject(name),
  });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Projet introuvable.</p>;
  const p = data.project;
  return (
    <div>
      <p><Link to="/projects">← Projets</Link></p>
      <h2>{p.name}</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <KpiCard label="Sessions" value={String(p.session_count)} />
        <KpiCard label="Tokens" value={formatTokens(p.usage.input + p.usage.output)} />
        <KpiCard label="Coût" value={formatCost(p.cost, "€", p.cost_known)} />
      </div>
      <h3>Sessions</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Titre / ID</th><th>Modèle</th><th>Durée</th><th>Tokens</th><th>Coût</th></tr>
        </thead>
        <tbody>
          {data.sessions.map((s) => (
            <tr key={s.session_id}>
              <td>
                <Link to={`/sessions/${encodeURIComponent(s.session_id)}`}>
                  {s.ai_title ?? s.session_id}
                </Link>
                {s.is_active && <span style={{ color: "#16a34a" }}> ● live</span>}
              </td>
              <td align="center">{s.models[0] ?? "—"}</td>
              <td align="center">{formatDuration(s.duration_seconds)}</td>
              <td align="center">{formatTokens(s.usage.input + s.usage.output)}</td>
              <td align="center">{formatCost(s.cost, "€", s.cost_known)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: Build, expect PASS**

Run: `cd frontend && npm run build`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Projects.tsx frontend/src/pages/ProjectDetail.tsx
git commit -m "feat(frontend): projects list and detail pages"
```

---

## Task 14: Session explorer page

**Files:**
- Modify: `frontend/src/pages/Session.tsx`

**Interfaces:**
- Consumes: `api/client.getSession`, `lib/format`, `MessageRecord`/`SessionSummary` types.
- Produces: Session page showing metadata (model, branch, version, duration, provider, tokens, cost) and a timeline of `messages` (type, timestamp, tools, content_kinds, per-message tokens).

- [ ] **Step 1: Write `frontend/src/pages/Session.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { getSession } from "../api/client";
import { formatCost, formatDuration, formatTokens } from "../lib/format";

export default function Session() {
  const { id = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["session", id],
    queryFn: () => getSession(id),
  });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Session introuvable.</p>;
  const s = data.summary;
  return (
    <div>
      <h2>{s.ai_title ?? s.session_id}</h2>
      <ul>
        <li>Projet : {s.project}</li>
        <li>Modèle(s) : {s.models.join(", ") || "—"} ({s.provider})</li>
        <li>Branche : {s.git_branch ?? "—"} · CC {s.cc_version ?? "—"}</li>
        <li>Durée : {formatDuration(s.duration_seconds)} · Messages : {s.message_count}</li>
        <li>Tokens : {formatTokens(s.usage.input + s.usage.output)} · Coût : {formatCost(s.cost, "€", s.cost_known)}</li>
      </ul>
      <h3>Timeline</h3>
      <ol>
        {data.messages.map((m, i) => (
          <li key={m.uuid ?? i} style={{ marginBottom: 6 }}>
            <strong>{m.type}</strong>{" "}
            <span style={{ color: "#666" }}>{m.timestamp?.slice(11, 19) ?? ""}</span>
            {m.tools.length > 0 && <span> · 🔧 {m.tools.join(", ")}</span>}
            {m.content_kinds.length > 0 && <span> · {m.content_kinds.join("/")}</span>}
            {(m.usage.input + m.usage.output) > 0 && (
              <span> · {formatTokens(m.usage.input + m.usage.output)} tok</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
```

- [ ] **Step 2: Build, expect PASS**

Run: `cd frontend && npm run build`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Session.tsx
git commit -m "feat(frontend): session explorer page"
```

---

## Task 15: Live page (SSE) + README

**Files:**
- Create: `frontend/src/api/sse.ts`, `README.md`
- Modify: `frontend/src/pages/Live.tsx`

**Interfaces:**
- Consumes: `SessionSummary` type, `lib/format`.
- Produces:
  - `sse.ts`: `subscribeLive(onSnapshot: (snap: { active: SessionSummary[]; generated_at: string }) => void): () => void` — opens `EventSource` to `${BASE}/api/live`, parses each event, returns an unsubscribe fn; on error, closes and retries after 3s (polling fallback documented in README).
  - `Live` page: subscribes on mount, shows active sessions with live tokens, last tool, model, elapsed; shows "aucune session active" when empty.
  - `README.md`: how to run backend (`uv run uvicorn app.main:app`) and frontend (`npm run dev`), config env vars, pricing.json editing, export contract.

- [ ] **Step 1: Create `frontend/src/api/sse.ts`**

```typescript
import type { SessionSummary } from "./client";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface LiveSnapshot {
  active: SessionSummary[];
  generated_at: string;
}

export function subscribeLive(onSnapshot: (snap: LiveSnapshot) => void): () => void {
  let source: EventSource | null = null;
  let retry: ReturnType<typeof setTimeout> | null = null;
  let closed = false;

  const connect = () => {
    source = new EventSource(`${BASE}/api/live`);
    source.onmessage = (e) => onSnapshot(JSON.parse(e.data));
    source.onerror = () => {
      source?.close();
      if (!closed) retry = setTimeout(connect, 3000);
    };
  };
  connect();

  return () => {
    closed = true;
    source?.close();
    if (retry) clearTimeout(retry);
  };
}
```

- [ ] **Step 2: Write `frontend/src/pages/Live.tsx`**

```tsx
import { useEffect, useState } from "react";

import type { SessionSummary } from "../api/client";
import { subscribeLive } from "../api/sse";
import { formatTokens } from "../lib/format";

export default function Live() {
  const [active, setActive] = useState<SessionSummary[]>([]);
  const [updated, setUpdated] = useState<string>("");

  useEffect(() => {
    const unsub = subscribeLive((snap) => {
      setActive(snap.active);
      setUpdated(snap.generated_at);
    });
    return unsub;
  }, []);

  return (
    <div>
      <h2>Sessions actives <span style={{ color: "#16a34a" }}>●</span></h2>
      <p style={{ color: "#666" }}>Dernière mise à jour : {updated.slice(11, 19) || "…"}</p>
      {active.length === 0 ? (
        <p>Aucune session active.</p>
      ) : (
        <ul>
          {active.map((s) => {
            const tool = Object.keys(s.tool_counts).slice(-1)[0] ?? "—";
            return (
              <li key={s.session_id} style={{ marginBottom: 8 }}>
                <strong>{s.ai_title ?? s.session_id}</strong> — {s.project}
                <br />
                {s.models[0] ?? "—"} · {formatTokens(s.usage.input + s.usage.output)} tok ·
                dernier outil : {tool} · {s.message_count} messages
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create `README.md`**

```markdown
# CCDashboard

Dashboard local pour monitorer les sessions Claude Code (`~/.claude/projects`).

## Backend (FastAPI, uv)

    cd backend
    uv sync
    uv run uvicorn app.main:app --reload --port 8000

Tests : `cd backend && uv run pytest`

## Frontend (React + Vite)

    cd frontend
    npm install
    npm run dev    # http://localhost:5173

Build : `npm run build` · Tests : `npm test`

## Configuration (env, préfixe `CCDASH_`)

| Variable | Défaut | Rôle |
|---|---|---|
| `CCDASH_PROJECTS_DIR` | `~/.claude/projects` | dossier source |
| `CCDASH_CURRENCY` | `€` | devise affichée |
| `CCDASH_LIVE_ACTIVE_THRESHOLD_SECONDS` | `30` | seuil "session active" |
| `CCDASH_EXPORT_ENABLED` | `false` | active l'export central |
| `CCDASH_EXPORT_ENDPOINT` | — | URL POST du serveur central |
| `CCDASH_EXPORT_TOKEN` | — | bearer token |
| `CCDASH_EXPORT_INTERVAL_MINUTES` | `15` | période d'envoi |
| `CCDASH_EXPORT_INCLUDE_ENRICHED` | `false` | inclut titres/branche/version |
| `CCDASH_EXPORT_MACHINE_ID` / `_USER_ID` / `_INSTANCE_ID` | hostname / `unknown` / `default` | identité source |

## Prix

Éditer `pricing.json` (par million de tokens, par fournisseur/modèle). Un modèle
absent ⇒ coût marqué incomplet dans l'UI (jamais 0 silencieux).

## Export central (contrat de payload, projet futur)

`POST <endpoint>` avec `Authorization: Bearer <token>`, body :

    {
      "schema_version": 1,
      "source": {"machine_id": "...", "user_id": "...", "instance_id": "..."},
      "sent_at": "<iso>",
      "sessions": [ /* agrégats; enrichis si activés */ ],
      "projects": [ /* agrégats */ ]
    }

Envoi incrémental (curseur par session), agrégats seuls par défaut. Le SSE `/api/live`
bascule en reconnexion auto si la connexion tombe.
```

- [ ] **Step 4: Build frontend, expect PASS**

Run: `cd frontend && npm run build && npm test`

- [ ] **Step 5: End-to-end smoke test**

Run backend (`cd backend && uv run uvicorn app.main:app --port 8000 &`) and frontend (`cd frontend && npm run dev`). Open `http://localhost:5173`, confirm Overview loads real data, navigate to a project → session, open Live. Stop servers afterward.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/sse.ts frontend/src/pages/Live.tsx README.md
git commit -m "feat(frontend): live page (SSE) and README"
```

---

## Task 16: Browser end-to-end smoke test (Playwright)

**Files:**
- Create: `frontend/tests/e2e/dashboard.spec.ts`, `frontend/playwright.config.ts`
- Modify: `frontend/package.json` (add `@playwright/test` devDep + `test:e2e` script)
- Create: `docs/superpowers/e2e-screenshots/` (output dir for captured screenshots, gitignored)

**Purpose:** Verify the real, running app in a browser end-to-end — not just unit tests. The dashboard reads the live `~/.claude/projects` data on this machine, so the test runs against real session data and asserts the four areas render.

**Interfaces:**
- Consumes the running backend (`uvicorn app.main:app` on port 8000) and frontend dev server (`vite` on port 5173). Playwright's `webServer` config starts both automatically.

**Approach:** Use `@playwright/test` (Chromium). `playwright.config.ts` declares two `webServer` entries (backend + frontend) so `npx playwright test` boots them, waits for readiness, runs the spec, and tears them down. The spec is resilient to variable real data: it asserts on structure (headings, nav, table presence, row counts ≥ 0) rather than exact values, and captures screenshots for visual confirmation.

- [ ] **Step 1: Add dependency and script**

In `frontend/package.json` add to devDependencies `"@playwright/test": "^1.45.0"` and to scripts `"test:e2e": "playwright test"`. Then run `cd frontend && npm install && npx playwright install chromium`.

- [ ] **Step 2: Create `frontend/playwright.config.ts`**

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/api/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --port 5173",
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
```

- [ ] **Step 3: Write the e2e spec `frontend/tests/e2e/dashboard.spec.ts`**

```typescript
import { expect, test } from "@playwright/test";

const SHOTS = "../docs/superpowers/e2e-screenshots";

test("overview loads and shows KPIs", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "CCDashboard" })).toBeVisible();
  // KPI labels from Overview.tsx
  await expect(page.getByText("Sessions")).toBeVisible();
  await expect(page.getByText("Coût total")).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/overview.png`, fullPage: true });
});

test("navigate Projects -> ProjectDetail -> Session", async ({ page }) => {
  await page.goto("/projects");
  await expect(page.getByRole("heading", { name: "Projets" })).toBeVisible();
  const firstProjectLink = page.locator("table a").first();
  await expect(firstProjectLink).toBeVisible();
  await firstProjectLink.click();
  // ProjectDetail: sessions table; click first session if any
  await expect(page.getByRole("heading", { name: "Sessions" })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/project-detail.png`, fullPage: true });
  const firstSession = page.locator("table a").first();
  if (await firstSession.count()) {
    await firstSession.click();
    await expect(page.getByRole("heading", { name: "Timeline" })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/session.png`, fullPage: true });
  }
});

test("live page renders", async ({ page }) => {
  await page.goto("/live");
  await expect(page.getByRole("heading", { name: /Sessions actives/ })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/live.png`, fullPage: true });
});
```

- [ ] **Step 4: Gitignore screenshots and Playwright artifacts**

Add to root `.gitignore`: `docs/superpowers/e2e-screenshots/`, `frontend/playwright-report/`, `frontend/test-results/`.

- [ ] **Step 5: Run the e2e suite**

Run: `cd frontend && npx playwright test`
Expected: 3 passed (or the session step skipped if no sessions exist). The webServer config boots backend + frontend automatically. Screenshots written to `docs/superpowers/e2e-screenshots/`.

- [ ] **Step 6: Commit**

```bash
git add frontend/playwright.config.ts frontend/tests/e2e frontend/package.json frontend/package-lock.json .gitignore
git commit -m "test(frontend): browser end-to-end smoke test with Playwright"
```

---

## Self-Review

**Spec coverage:**
- §1 Architecture → Tasks 1–15 (backend modules + frontend structure). ✓
- §2 Data model (MessageRecord/SessionSummary/ProjectSummary/temporal) → Tasks 2, 3, 5, 7. ✓
- §3 Cost & provider (configurable table, formula, unknown-model flag) → Task 4; surfaced in UI Tasks 12–14 via `UnknownCostBadge`. ✓
- §4 Live (active threshold, watcher, SSE, polling fallback) → Tasks 9 (backend), 15 (frontend + fallback). ✓
- §5 Error handling (corrupt lines, missing usage, unknown model, unreadable file, SSE reconnect) → Tasks 3, 4, 6 (`OSError` skip), 15. ✓
- §6 Tests (parser/metrics/pricing/exporter + frontend smoke) → every backend task is TDD; frontend Tasks 11–12 have Vitest tests. ✓
- §7 Export (disabled default, aggregates-only, enriched opt-in, identity, periodic, incremental cursor, versioned payload, mockable) → Task 10. ✓
- Config synthesis → Task 1 + README (Task 15). ✓

**Placeholder scan:** No "TBD/TODO". The only intentional placeholders are the page stubs in Task 11 Step 9, each fully replaced in Tasks 12–15. Acceptable (needed for compilation ordering).

**Type consistency:** Backend names verified consistent across tasks — `Usage.add`, `parse_session_file`/`parse_lines`/`ParsedSession`, `summarize_session(**kwargs)`, `PriceTable.load`/`cost_for_usage`, `detect_provider`, `SessionStore.all_summaries`/`get_summary`, `build_overview`/`list_projects`/`project_detail`, `live_snapshot`/`active_sessions`, `Exporter.send_once`/`pending`/`run_periodic`/`build_payload`. Frontend types in `api/client.ts` mirror backend model fields one-to-one; `formatCost(n, currency, known)` signature used consistently across Tasks 12–14.
```
