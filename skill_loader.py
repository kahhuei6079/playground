"""Load Cursor-style SKILL.md folders into office agent system prompts."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import yaml

import config
from config import ROOT
from model_config import AGENT_IDS

_CURSOR_SKILLS_HEADER = re.compile(
    r"^##\s+Cursor\s+skills\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _cursor_skill_roots() -> list[Path]:
    roots: list[Path] = []
    personal = Path.home() / ".cursor" / "skills"
    if personal.is_dir():
        roots.append(personal)
    project = ROOT / ".cursor" / "skills"
    if project.is_dir():
        roots.append(project)
    for part in (os.environ.get("AGENT_OFFICE_SKILL_DIRS") or "").split(os.pathsep):
        part = part.strip()
        if part:
            roots.append(Path(part).expanduser())
    return roots


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return meta if isinstance(meta, dict) else {}, body


def _strip_frontmatter(text: str) -> str:
    _, body = _split_frontmatter(text)
    return body


def _refs_from_meta(meta: dict) -> list[str]:
    raw = meta.get("cursor_skills") or meta.get("cursor_skill") or []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        return [str(r).strip() for r in raw if str(r).strip()]
    return []


def _refs_from_body(body: str) -> tuple[list[str], str]:
    """Optional ## Cursor skills section with - skill-name bullets; returns refs and body without that section."""
    match = _CURSOR_SKILLS_HEADER.search(body)
    if not match:
        return [], body
    before = body[: match.start()].strip()
    section = body[match.end() :].strip()
    refs: list[str] = []
    tail: list[str] = []
    for line in section.splitlines():
        m = re.match(r"^[-*]\s+`?([^`#\s]+)`?", line.strip())
        if m:
            refs.append(m.group(1).strip())
        elif line.strip():
            tail.append(line)
    local = before
    if tail:
        local = f"{local}\n\n" + "\n".join(tail).strip() if local else "\n".join(tail).strip()
    return refs, local


def _agent_skill_path(agent: str) -> Path | None:
    for name in ("SKILL.md", "skill.md"):
        path = config.AGENTS_DIR / agent / name
        if path.is_file():
            return path
    return None


def load_agent_skill_file(agent: str) -> tuple[list[str], str, str]:
    """Returns (cursor_skill_refs, local_markdown_body, source_path)."""
    path = _agent_skill_path(agent)
    if not path:
        return [], "", ""
    raw = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(raw)
    refs = list(_refs_from_meta(meta))
    section_refs, body = _refs_from_body(body)
    for r in section_refs:
        if r not in refs:
            refs.append(r)
    return refs, body.strip(), str(path)


def resolve_skill_dir(ref: str) -> Path | None:
    ref = (ref or "").strip()
    if not ref:
        return None
    path = Path(ref).expanduser()
    if path.is_file() and path.name.lower() == "skill.md":
        return path.parent
    if path.is_dir() and (path / "SKILL.md").is_file():
        return path
    if path.is_dir() and (path / "skill.md").is_file():
        return path
    for root in _cursor_skill_roots():
        candidate = root / ref
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


@lru_cache
def load_skills_config() -> dict:
    path = Path(config.SKILLS_CONFIG_PATH)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _refs_from_skills_yaml(agent: str) -> list[str]:
    cfg = load_skills_config()
    refs = cfg.get(agent)
    if refs is None and isinstance(cfg.get("agents"), dict):
        refs = cfg["agents"].get(agent)
    if not refs:
        return []
    if isinstance(refs, str):
        return [refs]
    if isinstance(refs, list):
        return [str(r).strip() for r in refs if str(r).strip()]
    return []


def skill_refs_for_agent(agent: str) -> list[str]:
    """Merged refs: agents/<role>/SKILL.md first, then skills.yaml (deduped)."""
    agent_refs, _, _ = load_agent_skill_file(agent)
    merged: list[str] = []
    for ref in agent_refs + _refs_from_skills_yaml(agent):
        if ref not in merged:
            merged.append(ref)
    return merged


def _resolved_skill_blocks(refs: list[str]) -> list[str]:
    blocks: list[str] = []
    for ref in refs:
        skill_dir = resolve_skill_dir(ref)
        if not skill_dir:
            blocks.append(
                f"### `{ref}`\n\n(Skill not found. Check the ref in agents/*/SKILL.md or skills.yaml "
                "and ~/.cursor/skills/ or .cursor/skills/.)"
            )
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            skill_md = skill_dir / "skill.md"
        raw = skill_md.read_text(encoding="utf-8")
        body = _strip_frontmatter(raw)
        blocks.append(f"### {skill_dir.name}\n\n{body}")
    return blocks


def load_cursor_skills_text(agent: str) -> str:
    if agent not in AGENT_IDS:
        return ""
    _, local_body, agent_path = load_agent_skill_file(agent)
    refs = skill_refs_for_agent(agent)
    blocks = _resolved_skill_blocks(refs)

    parts: list[str] = []
    if local_body or agent_path:
        header = f"## Agent skills ({agent_path or f'agents/{agent}/SKILL.md'})"
        parts.append(f"{header}\n\n{local_body or '(No local notes — only Cursor skill references below.)'}")
    if blocks:
        parts.append(
            "## Bound Cursor skills\n\n"
            "Resolved from `cursor_skills` in the agent SKILL.md and/or `skills.yaml`. "
            "Follow when they do not conflict with SOUL, supervised gates, or JSON schemas.\n\n"
            + "\n\n---\n\n".join(blocks)
        )
    if not parts:
        return ""
    return "\n\n".join(parts)


def list_agent_skill_bindings() -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for agent in AGENT_IDS:
        agent_refs, _, agent_path = load_agent_skill_file(agent)
        entries: list[dict[str, str]] = []
        for ref in agent_refs:
            skill_dir = resolve_skill_dir(ref)
            entries.append(
                {
                    "ref": ref,
                    "source": "agent_skill",
                    "resolved": str(skill_dir) if skill_dir else "",
                    "ok": bool(skill_dir),
                }
            )
        for ref in _refs_from_skills_yaml(agent):
            if ref in agent_refs:
                continue
            skill_dir = resolve_skill_dir(ref)
            entries.append(
                {
                    "ref": ref,
                    "source": "skills.yaml",
                    "resolved": str(skill_dir) if skill_dir else "",
                    "ok": bool(skill_dir),
                }
            )
        out[agent] = entries
    return out


def reload_skills_config() -> None:
    load_skills_config.cache_clear()
