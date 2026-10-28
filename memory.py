from datetime import datetime, timezone
from pathlib import Path

from config import AGENTS_DIR, SHARED_DIR, WORKSPACE_DIR


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_soul(agent: str) -> str:
    return _read(AGENTS_DIR / agent / "SOUL.md")


def load_private_memory(agent: str) -> str:
    return _read(AGENTS_DIR / agent / "MEMORY.md")


def load_shared() -> str:
    parts = []
    for name in ("PRINCIPLES.md", "LESSONS.md", "PROJECT_CONTEXT.md", "DECISIONS.md", "TASK_BOARD.md"):
        path = SHARED_DIR / name
        if path.exists():
            parts.append(f"# {name}\n\n{_read(path).strip()}")
    return "\n\n---\n\n".join(parts)


def workspace_for(thread_id: str) -> Path:
    path = WORKSPACE_DIR / thread_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_workspace_paths(thread_id: str) -> list[str]:
    root = workspace_for(thread_id)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def list_workspace_files(thread_id: str) -> dict[str, str]:
    root = workspace_for(thread_id)
    files: dict[str, str] = {}
    for rel in list_workspace_paths(thread_id):
        path = root / rel
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            files[rel] = f"[binary file: {path.name}]"
    return files


def _html_preview_path(paths: list[str]) -> str | None:
    if not paths:
        return None
    for name in ("index.html", "index.htm", "main.html"):
        if name in paths:
            return name
    for rel in paths:
        if rel.lower().endswith(".html"):
            return rel
    return None


def deliverable_info(thread_id: str) -> dict[str, str | list[str] | None]:
    paths = list_workspace_paths(thread_id)
    preview = _html_preview_path(paths)
    root = workspace_for(thread_id)
    preview_url = f"/preview/{thread_id}/{preview}" if preview else None
    return {
        "folder": str(root),
        "relative_folder": f"workspace/{thread_id}",
        "files": paths,
        "preview_path": preview,
        "preview_url": preview_url,
        "has_html_preview": bool(preview),
    }


def open_workspace_folder(thread_id: str) -> str:
    import platform
    import subprocess

    root = workspace_for(thread_id)
    if not root.is_dir():
        raise FileNotFoundError(f"No workspace folder for thread {thread_id}")
    path = str(root.resolve())
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", path], check=True)
    elif system == "Windows":
        subprocess.run(["explorer", path], check=True)
    else:
        subprocess.run(["xdg-open", path], check=True)
    return path


def _safe_relative_path(thread_id: str, raw: str) -> Path:
    rel = Path(str(raw).strip().lstrip("/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Refusing unsafe path: {raw}")
    prefixes = [
        Path("workspace") / thread_id,
        Path("workspace"),
        Path(thread_id),
    ]
    for prefix in prefixes:
        try:
            rel = rel.relative_to(prefix)
        except ValueError:
            continue
        else:
            break
    if not rel.parts:
        raise ValueError(f"Refusing empty path: {raw}")
    return rel


def write_workspace_files(thread_id: str, files: list[dict]) -> list[str]:
    root = workspace_for(thread_id)
    written = []
    for item in files:
        rel = _safe_relative_path(thread_id, item["path"])
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(item.get("content", ""), encoding="utf-8")
        written.append(rel.as_posix())
    return written


MAX_SESSION_LESSONS = 30
_SESSION_HEADING = "## Session memory"


def _clip(text: str, limit: int = 280) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _section_bullets(text: str, heading: str) -> tuple[str, list[str], str]:
    if heading not in text:
        return text.rstrip() + "\n\n", [], ""
    before, _, after = text.partition(heading)
    body: list[str] = []
    rest: list[str] = []
    started = False
    for line in after.splitlines():
        if not started and not line.strip():
            continue
        started = True
        if line.startswith("## "):
            rest = [line, *after.splitlines()[after.splitlines().index(line) + 1 :]]
            break
        body.append(line)
    bullets = [line for line in body if line.startswith("- ")]
    return before.rstrip() + "\n\n", bullets, ("\n".join(rest).rstrip() + "\n") if rest else ""


def _write_section(path: Path, preamble: str, bullets: list[str]) -> None:
    text = _read(path)
    if not text.strip():
        text = preamble.rstrip() + "\n"
    before, existing, rest = _section_bullets(text, _SESSION_HEADING)
    if _SESSION_HEADING not in text:
        before = text.rstrip() + "\n\n"
        existing = []
        rest = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = _SESSION_HEADING + "\n\n" + "\n".join(bullets) + "\n"
    tail = f"\n{rest}" if rest.strip() else ""
    path.write_text(before + body + tail, encoding="utf-8")


def lesson_count() -> int:
    text = _read(SHARED_DIR / "LESSONS.md")
    _, bullets, _ = _section_bullets(text, _SESSION_HEADING)
    return len(bullets)


def record_lesson(agent: str | None, text: str, *, thread_id: str = "", kind: str = "context") -> None:
    """Persist a short lesson. New sessions load this; the chat itself starts empty."""
    lesson = _clip(text)
    if not lesson:
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    who = agent or "office"
    bullet = f"- [{stamp}] {who} · {kind}: {lesson}"
    if thread_id:
        bullet += f" (`{thread_id}`)"

    shared = SHARED_DIR / "LESSONS.md"
    shared_text = _read(shared)
    _, shared_bullets, _ = _section_bullets(shared_text, _SESSION_HEADING)
    if any(lesson in item for item in shared_bullets[-8:]):
        return
    shared_bullets.append(bullet)
    _write_section(
        shared,
        "# Lessons\n\n"
        "A new session starts with an empty conversation.\n"
        "These lines are the carry-over: mistakes to avoid, and context that still applies.\n",
        shared_bullets[-MAX_SESSION_LESSONS:],
    )
    if not agent:
        return
    private = AGENTS_DIR / agent / "MEMORY.md"
    _, private_bullets, _ = _section_bullets(_read(private), _SESSION_HEADING)
    private_bullets.append(bullet)
    _write_section(
        private,
        f"# {agent.upper()} memory\n\n"
        "Session chat does not carry over. This section does.\n",
        private_bullets[-MAX_SESSION_LESSONS:],
    )


def append_private_memory(agent: str, notes: list[str]) -> None:
    for note in notes:
        record_lesson(agent, note, kind="context")


def list_tasks() -> list[dict[str, str]]:
    """Newest task first, from the shared board."""
    path = SHARED_DIR / "TASK_BOARD.md"
    rows: list[dict[str, str]] = []
    for raw in _read(path).splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Thread"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0] in {"Thread", "---"}:
            continue
        row = {
            "thread_id": cells[0],
            "task": cells[1],
            "status": cells[2],
            "owner": cells[3],
            "updated": cells[4],
        }
        info = deliverable_info(row["thread_id"])
        if info.get("files"):
            row["preview_url"] = info.get("preview_url") or ""
            row["folder"] = str(info.get("folder") or "")
        row["can_continue"] = row["status"] in ("blocked", "revising", "awaiting_release")
        rows.append(row)
    rows.reverse()
    return rows


def update_task_board(thread_id: str, task: str, status: str, owner: str) -> None:
    path = SHARED_DIR / "TASK_BOARD.md"
    existing = _read(path)
    line = f"| `{thread_id}` | {task.replace('|', '/')} | {status} | {owner} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC |"
    if f"| `{thread_id}` |" in existing:
        lines = []
        for raw in existing.splitlines():
            if raw.startswith(f"| `{thread_id}` |"):
                lines.append(line)
            else:
                lines.append(raw)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _emit_tasks_updated(thread_id)
        return
    if existing.strip():
        path.write_text(existing.rstrip() + "\n" + line + "\n", encoding="utf-8")
    else:
        path.write_text(
            "# Task Board\n\n| Thread | Task | Status | Owner | Updated |\n| --- | --- | --- | --- | --- |\n"
            + line
            + "\n",
            encoding="utf-8",
        )
    _emit_tasks_updated(thread_id)


def _emit_tasks_updated(thread_id: str) -> None:
    try:
        from events import emit, thread_id_var

        token = thread_id_var.set(thread_id)
        try:
            emit({"type": "tasks_updated", "thread_id": thread_id})
        finally:
            thread_id_var.reset(token)
    except Exception:  # noqa: BLE001
        pass
