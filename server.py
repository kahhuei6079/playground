from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from queue import Empty

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import MODELS_CONFIG_PATH, OFFICE_CONFIG_PATH, ROOT, SKILLS_CONFIG_PATH
from office_config import office_public_view, reload_office_config
from model_config import default_profile, list_agent_models, reload_models_config
from skill_loader import list_agent_skill_bindings, reload_skills_config
from events import hub
from memory import (
    _safe_relative_path,
    deliverable_info,
    lesson_count,
    list_tasks,
    list_workspace_files,
    open_workspace_folder,
    workspace_for,
)

_THREAD_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
from runtime import (
    continue_thread,
    force_stop,
    is_busy,
    list_active_runs,
    open_release_gate_if_needed,
    resume_task,
    snapshot,
    start_task,
)

STATIC = ROOT / "static"
app = FastAPI(title="Agent Office")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class RunRequest(BaseModel):
    task: str
    thread_id: str | None = None


class DecisionRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: str = Field(default="")


class StopRequest(BaseModel):
    thread_id: str | None = None
    all: bool = Field(default=False, description="Stop every active run in this office")


class ContinueRequest(BaseModel):
    note: str = Field(default="", description="Optional note for PM triage when continuing")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/dev/animation")
def dev_animation_smoke() -> RedirectResponse:
    """Visual runner for office parcel / meeting animation smoke tests."""
    return RedirectResponse(url="/static/animation-smoke.html", status_code=302)


@app.get("/api/meta")
def meta() -> dict:
    reload_models_config()
    reload_skills_config()
    reload_office_config()
    default = default_profile().public_view()
    office = office_public_view()
    return {
        "model": f"{default['provider']}/{default['model']}",
        "default": default,
        "agents": list_agent_models(),
        "models_config": MODELS_CONFIG_PATH,
        "skills_config": SKILLS_CONFIG_PATH,
        "office_config": OFFICE_CONFIG_PATH,
        "office": office,
        "cursor_skills": list_agent_skill_bindings(),
        "memory_lessons": lesson_count(),
    }


@app.post("/api/run")
def api_run(body: RunRequest) -> dict:
    if not body.task.strip():
        raise HTTPException(400, "Task is required")
    thread_id = start_task(body.task.strip(), body.thread_id)
    return {"thread_id": thread_id}


@app.post("/api/stop")
def api_stop(body: StopRequest) -> dict:
    if body.thread_id:
        _check_thread_id(body.thread_id)
    result = force_stop(body.thread_id, all_runs=body.all)
    return {"ok": True, **result}


@app.get("/api/active")
def api_active() -> dict:
    return {"active": list_active_runs()}


@app.post("/api/decide")
def api_decide(body: DecisionRequest) -> dict:
    if is_busy(body.thread_id):
        raise HTTPException(409, "This thread is still running. Wait a moment and try again.")
    if not body.approved and not body.feedback.strip():
        raise HTTPException(400, "Rejection requires feedback")
    try:
        resume_task(body.thread_id, body.approved, body.feedback.strip())
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"thread_id": body.thread_id, "approved": body.approved}


@app.get("/api/tasks")
def api_tasks() -> dict:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        {"tasks": list_tasks()},
        headers={"Cache-Control": "no-store"},
    )


def _check_thread_id(thread_id: str) -> None:
    if not _THREAD_ID.fullmatch(thread_id):
        raise HTTPException(400, "Invalid thread id")


@app.post("/api/thread/{thread_id}/open-release-gate")
def api_open_release_gate(thread_id: str) -> dict:
    _check_thread_id(thread_id)
    if is_busy(thread_id):
        raise HTTPException(409, "This thread is still running. Wait a moment and try again.")
    opened = open_release_gate_if_needed(thread_id)
    return {"ok": True, "thread_id": thread_id, "opened": opened}


@app.post("/api/thread/{thread_id}/continue")
def api_continue_thread(thread_id: str, body: ContinueRequest | None = None) -> dict:
    _check_thread_id(thread_id)
    note = (body.note if body else "") or ""
    try:
        continue_thread(thread_id, note.strip())
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "thread_id": thread_id}


@app.post("/api/thread/{thread_id}/open-folder")
def api_open_folder(thread_id: str) -> dict:
    _check_thread_id(thread_id)
    try:
        folder = open_workspace_folder(thread_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(500, f"Could not open folder: {exc}") from exc
    return {"ok": True, "folder": folder}


@app.get("/preview/{thread_id}/{file_path:path}")
def preview_file(thread_id: str, file_path: str) -> FileResponse:
    _check_thread_id(thread_id)
    if ".." in Path(file_path).parts:
        raise HTTPException(400, "Invalid path")
    try:
        rel = _safe_relative_path(thread_id, file_path or "index.html")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    target = workspace_for(thread_id) / rel
    if not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target)


@app.get("/api/thread/{thread_id}")
def api_thread(thread_id: str) -> dict:
    data = snapshot(thread_id)
    data["files"] = list_workspace_files(thread_id)
    data["deliverable"] = deliverable_info(thread_id)
    return data


@app.get("/api/stream")
async def api_stream(thread_id: str = "*") -> StreamingResponse:
    queue = hub.subscribe(thread_id)

    async def generate():
        loop = asyncio.get_running_loop()
        try:
            while True:
                try:
                    event = await loop.run_in_executor(None, lambda: queue.get(timeout=15))
                except Empty:
                    yield ": ping\n\n"
                    continue
                yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            hub.unsubscribe(queue, thread_id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")
