from __future__ import annotations

import asyncio
import json
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.exporter import Exporter
from app.metrics import build_overview, list_projects, project_detail
from app.parser import parse_session_file
from app.store import SessionStore
from app.watcher import live_snapshot

app = FastAPI(title="CCDashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=get_settings().cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_store() -> SessionStore:
    return SessionStore(get_settings())


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def config():
    return {"currency": get_settings().currency}


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
            messages = store.with_message_costs(parsed.records, summary.provider)
            return {"summary": summary, "messages": messages}
    raise HTTPException(status_code=404, detail="session not found")


@app.get("/api/live")
async def live(store: SessionStore = Depends(get_store)):
    async def event_generator():
        while True:
            yield {"data": json.dumps(live_snapshot(store))}
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())


@app.on_event("startup")
async def _start_exporter():
    settings = get_settings()
    if settings.export_enabled and settings.export_endpoint:
        exporter = Exporter(settings, get_store())
        asyncio.create_task(exporter.run_periodic())
