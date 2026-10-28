"""Heuristics for scope escalation — avoid pointless designer↔PM loops on non-UI work."""

from __future__ import annotations

from typing import Any


def plan_text_blob(plan: dict[str, Any]) -> str:
    parts = [plan.get("goal", ""), plan.get("scope", "")]
    parts.extend(plan.get("requirements") or [])
    parts.extend(plan.get("out_of_scope") or [])
    parts.extend(plan.get("acceptance_criteria") or [])
    return " ".join(str(p) for p in parts).lower()


def plan_is_non_ui(plan: dict[str, Any]) -> bool:
    blob = plan_text_blob(plan)
    if any(x in blob for x in ("no ui", "no ux", "without ui", "without ux", "no user interface")):
        return True
    non_ui = (
        "console",
        "command line",
        "cli ",
        " cli",
        "terminal",
        "stdout",
        "hello world",
        ".jar",
        "java application",
        "batch script",
        "shell script",
        "backend only",
        "api only",
        "runnable java",
    )
    ui = ("html", "web page", "browser", "button", "css", "frontend", " ui ", "screens", "mockup")
    has_non = any(h in blob for h in non_ui)
    has_ui = any(h in blob for h in ui)
    return has_non and not has_ui


def needs_designer_track(state: dict[str, Any]) -> bool:
    """Whether the Designer step should run (scope agreement overrides plan heuristics)."""
    agreement = state.get("scope_agreement") or {}
    if "needs_designer" in agreement:
        return bool(agreement["needs_designer"])
    plan = state.get("plan") or {}
    return not plan_is_non_ui(plan)


def minimal_design_spec(state: dict[str, Any]) -> dict[str, Any]:
    agreement = state.get("scope_agreement") or {}
    arch = state.get("architecture_brief") or {}
    ptype = agreement.get("project_type") or arch.get("project_type") or "mixed"
    return {
        "product_intent": agreement.get("aligned_summary")
        or arch.get("summary")
        or "Deliverable per PM plan and architect scope.",
        "scope_ok": True,
        "user_flows": [
            "Operator uses the deliverable as described in acceptance criteria "
            f"({ptype}).",
        ],
        "screens": ["N/A — no UI/UX design track for this slice"],
        "interaction_notes": [
            agreement.get("technical_approach") or arch.get("delivery_shape") or "",
        ],
        "ui_copy": [],
        "accessibility": [],
        "open_questions": [],
    }


def designer_escalation_is_no_ui_mismatch(esc: dict[str, str], plan: dict[str, Any]) -> bool:
    reason = (esc.get("reason") or "").lower()
    no_ui_excuse = any(
        p in reason
        for p in (
            "no ui",
            "no user interface",
            "no ux",
            "nothing to design",
            "no screens",
            "cli",
            "console",
            "command line",
            "terminal",
            "not a ui",
            "without ui",
            "ui/ux",
            "no graphical",
        )
    )
    return no_ui_excuse and plan_is_non_ui(plan)
