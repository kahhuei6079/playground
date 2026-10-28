from pathlib import Path

from skill_loader import load_cursor_skills_text, resolve_skill_dir, skill_refs_for_agent


def test_resolve_skill_dir_by_name(tmp_path, monkeypatch):
    skill_root = tmp_path / "skills"
    (skill_root / "demo-skill").mkdir(parents=True)
    (skill_root / "demo-skill" / "SKILL.md").write_text("---\nname: demo\n---\n\nHello skill.\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_OFFICE_SKILL_DIRS", str(skill_root))
    resolved = resolve_skill_dir("demo-skill")
    assert resolved == skill_root / "demo-skill"


def test_load_cursor_skills_includes_body(tmp_path, monkeypatch):
    skill_root = tmp_path / "skills"
    (skill_root / "dev-tip").mkdir(parents=True)
    (skill_root / "dev-tip" / "SKILL.md").write_text("---\nname: dev-tip\n---\n\nAlways run pytest.\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_OFFICE_SKILL_DIRS", str(skill_root))
    cfg = tmp_path / "skills.yaml"
    cfg.write_text("developer:\n  - dev-tip\n", encoding="utf-8")
    import config
    from skill_loader import reload_skills_config

    monkeypatch.setattr(config, "SKILLS_CONFIG_PATH", str(cfg))
    reload_skills_config()
    text = load_cursor_skills_text("developer")
    assert "Always run pytest" in text
    assert "Bound Cursor skills" in text


def test_skill_refs_empty_by_default():
    assert skill_refs_for_agent("pm") == []


def test_agent_skill_md_cursor_refs(tmp_path, monkeypatch):
    skill_root = tmp_path / "cursor-skills"
    (skill_root / "office-pytest").mkdir(parents=True)
    (skill_root / "office-pytest" / "SKILL.md").write_text("---\nname: x\n---\n\nRun pytest.\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_OFFICE_SKILL_DIRS", str(skill_root))

    agent_dir = tmp_path / "agents" / "qa"
    agent_dir.mkdir(parents=True)
    (agent_dir / "SKILL.md").write_text(
        "---\ncursor_skills:\n  - office-pytest\n---\n\nQA local note.\n",
        encoding="utf-8",
    )
    import config
    from skill_loader import reload_skills_config

    monkeypatch.setattr(config, "AGENTS_DIR", agent_dir.parent)
    reload_skills_config()
    text = load_cursor_skills_text("qa")
    assert "QA local note" in text
    assert "Run pytest" in text
    assert "office-pytest" in text
