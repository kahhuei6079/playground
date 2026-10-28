from typing import Any, Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agents import (
    run_architect_scope,
    run_architect_scope_reply,
    run_designer,
    run_developer,
    run_pm_ac_verification,
    run_pm,
    run_pm_discovery,
    run_pm_scope_alignment,
    run_qa,
)
from config import (
    CHECKPOINT_DB,
    DATA_DIR,
    MAX_QA_RETRIES,
    MAX_SCOPE_DIALOGUE_TURNS,
    MAX_SCOPE_ESCALATIONS,
)
from events import agent_var, emit, thread_id_var
from memory import record_lesson, update_task_board
from qa_runner import enrich_qa_report
from scope_policy import designer_escalation_is_no_ui_mismatch, minimal_design_spec, needs_designer_track
from state import OfficeState

ScopeTarget = Literal["pm", "designer", "developer"]


def _history(state: OfficeState, line: str) -> list[str]:
    return [*(state.get("history") or []), line]


def _step(
    state: OfficeState,
    text: str,
    *,
    kind: str = "work",
    from_agent: str = "",
    to_agent: str = "",
    direction: str = "",
) -> dict[str, Any]:
    entry: dict[str, Any] = {"kind": kind, "text": text}
    if from_agent:
        entry["from"] = from_agent
    if to_agent:
        entry["to"] = to_agent
    if direction:
        entry["direction"] = direction
    return {
        "history": _history(state, text),
        "activity": [*(state.get("activity") or []), entry],
    }


def _parse_escalation(payload: dict[str, Any] | None) -> dict[str, str] | None:
    if not payload:
        return None
    esc = payload.get("escalation")
    if not esc and payload.get("scope_ok") is not False:
        return None
    if not esc:
        return None
    if hasattr(esc, "model_dump"):
        esc = esc.model_dump()
    if not isinstance(esc, dict):
        return None
    target = esc.get("target")
    if target not in ("pm", "designer", "developer"):
        return None
    reason = (esc.get("reason") or "").strip() or "Scope or plan needs revision."
    return {"target": target, "reason": reason}


def _scope_limit_reached(state: OfficeState) -> bool:
    return int(state.get("scope_escalation_count") or 0) >= MAX_SCOPE_ESCALATIONS


def _remember(state: OfficeState, agent: str, kind: str, text: str) -> None:
    record_lesson(agent, text, thread_id=state.get("thread_id") or "", kind=kind)


def _scope_dialogue(state: OfficeState) -> list[dict[str, Any]]:
    return [d for d in (state.get("dialogue") or []) if d.get("phase") == "scope"]


def _append_scope_dialogue(
    state: OfficeState,
    from_agent: str,
    to_agent: str,
    text: str,
) -> dict[str, Any]:
    line = (text or "").strip()
    if not line:
        return {"dialogue": list(state.get("dialogue") or [])}
    entry = {"phase": "scope", "from": from_agent, "to": to_agent, "text": line}
    activity_entry = {
        "kind": "dialogue",
        "phase": "scope",
        "from": from_agent,
        "to": to_agent,
        "text": line,
    }
    return {
        "dialogue": [*(state.get("dialogue") or []), entry],
        "activity": [*(state.get("activity") or []), activity_entry],
        "history": _history(state, f"{from_agent} → {to_agent}: {line[:200]}"),
    }


def _last_scope_speaker(state: OfficeState) -> str:
    lines = _scope_dialogue(state)
    return (lines[-1].get("from") or "") if lines else ""


def _remember_notes(state: OfficeState, agent: str, payload: dict | None) -> None:
    for note in (payload or {}).get("memory_notes") or []:
        if str(note).strip():
            _remember(state, agent, "context", str(note))


def _is_release_rejection_triage(state: OfficeState) -> bool:
    if state.get("release_triage"):
        return True
    if state.get("escalation_from") == "release":
        return True
    return (state.get("feedback") or "").startswith("[Human rejected release]")


def _pm_return_after_release(state: OfficeState) -> str:
    note = (state.get("feedback") or "").lower()
    if needs_designer_track(state) and any(
        w in note for w in ("designer", "design spec", "ux track", "visual design", "wireframe")
    ):
        return "designer"
    return "developer"


def _pm_return_after_qa(state: OfficeState) -> str:
    """After QA escalates to PM, send work through Developer so tests can be added before re-test."""
    assessment = (state.get("test_results") or {}).get("validation_assessment") or {}
    if assessment.get("escalate_to") in ("pm", "developer") or assessment.get("kind") not in (None, "ok"):
        return "developer"
    feedback = (state.get("feedback") or "").lower()
    if any(k in feedback for k in ("test", "validation", "pytest", "qa cannot", "not runnable")):
        return "developer"
    return "qa"


def _escalation_update(state: OfficeState, from_agent: str, esc: dict[str, str]) -> dict[str, Any]:
    count = int(state.get("scope_escalation_count") or 0) + 1
    reason = esc["reason"]
    feedback = f"[Scope escalation from {from_agent}]\n{reason}"
    _remember(state, from_agent, "mistake", f"Scope was wrong for {esc['target']}: {reason}")
    _remember(state, esc["target"], "mistake", f"{from_agent} sent work back because scope was wrong: {reason}")
    return {
        "feedback": feedback,
        "escalation_from": from_agent,
        "escalation": esc,
        "scope_escalation_count": count,
        "plan_approved": False,
        "_handoff": {
            "from": from_agent,
            "to": esc["target"],
            "direction": "return",
            "reason": reason,
        },
    }


def pm_discover_node(state: OfficeState) -> dict:
    discovery = run_pm_discovery(state["task"])
    _remember_notes(state, "pm", discovery)
    questions = list(discovery.get("questions_for_human") or [])
    message = (discovery.get("message") or "").strip()
    assumptions = list(discovery.get("assumptions") or [])
    status = "awaiting_brief" if questions else "planning"
    update_task_board(state["thread_id"], state["task"], status, "pm")
    history_line = (
        "PM has questions before drafting the plan."
        if questions
        else "PM reviewed the brief — drafting the plan."
    )
    out: dict[str, Any] = {
        "brief_message": message,
        "brief_questions": questions,
        "brief_assumptions": assumptions,
        "current_agent": "pm",
        "status": status,
        **_step(
            state,
            history_line,
            kind="gate" if questions else "work",
            from_agent="pm",
            to_agent="human" if questions else "",
            direction="forward" if questions else "",
        ),
    }
    if questions:
        out["_handoff"] = {"from": "pm", "to": "human", "direction": "forward"}
    return out


def confirm_brief_node(state: OfficeState) -> dict:
    decision = interrupt(
        {
            "gate": "brief",
            "prompt": state.get("brief_message")
            or "The PM has a few questions before drafting the plan.",
            "message": state.get("brief_message") or "",
            "questions": state.get("brief_questions") or [],
            "assumptions": state.get("brief_assumptions") or [],
        }
    )
    feedback = decision.get("feedback", "") if isinstance(decision, dict) else str(decision)
    if isinstance(decision, dict) and not decision.get("approved") and not feedback.strip():
        feedback = "Proceed with your stated assumptions."
    brief_text = (
        "Human answered PM's briefing questions."
        if feedback.strip()
        else "Human asked PM to proceed with stated assumptions."
    )
    return {
        "brief_answers": feedback.strip(),
        "brief_confirmed": True,
        "feedback": "",
        "status": "planning",
        **_step(state, brief_text, kind="gate", from_agent="human", to_agent="architect", direction="forward"),
        "_handoff": {
            "from": "human",
            "to": "architect",
            "direction": "forward",
            "reason": "Brief confirmed — Architect opens scope",
        },
    }


def architect_node(state: OfficeState) -> dict:
    update_task_board(state["thread_id"], state["task"], "scoping", "architect")
    arch_brief = state.get("architecture_brief") or {}
    last = _last_scope_speaker(state)
    if arch_brief and last == "pm":
        reply = run_architect_scope_reply(
            state["task"],
            arch_brief,
            state.get("scope_agreement") or {},
            state.get("dialogue") or [],
            state.get("brief_answers") or "",
            state.get("brief_assumptions") or [],
        )
        _remember_notes(state, "architect", reply)
        if reply.get("project_type"):
            arch_brief = {**arch_brief, "project_type": reply["project_type"]}
        if reply.get("needs_designer") is not None:
            arch_brief = {**arch_brief, "needs_designer": reply["needs_designer"]}
        if reply.get("summary"):
            arch_brief = {**arch_brief, "summary": reply["summary"]}
        msg = reply.get("message") or ""
        dlg = _append_scope_dialogue(state, "architect", "pm", msg)
        state_for_handoff = {**state, **dlg, "architecture_brief": arch_brief}
        return {
            "architecture_brief": arch_brief,
            "architect_agrees": bool(reply.get("agrees_with_pm", True)),
            "current_agent": "architect",
            "status": "scoping",
            "scope_locked": False,
            **dlg,
            **_step(
                state_for_handoff,
                "Architect replied in the scope huddle.",
                kind="handoff",
                from_agent="architect",
                to_agent="pm",
                direction="forward",
            ),
            "_handoff": {
                "from": "architect",
                "to": "pm",
                "direction": "forward",
                "reason": "Scope huddle — PM responds",
            },
        }

    brief = run_architect_scope(
        state["task"],
        state.get("brief_answers") or "",
        state.get("brief_assumptions") or [],
    )
    _remember_notes(state, "architect", brief)
    ptype = brief.get("project_type") or "mixed"
    msg = brief.get("message_to_pm") or brief.get("summary") or ""
    dlg = _append_scope_dialogue(state, "architect", "pm", msg)
    state_for_handoff = {**state, **dlg}
    return {
        "architecture_brief": brief,
        "current_agent": "architect",
        "status": "scoping",
        "scope_locked": False,
        **dlg,
        **_step(
            state_for_handoff,
            f"Architect opened scope huddle ({ptype}).",
            kind="handoff",
            from_agent="architect",
            to_agent="pm",
            direction="forward",
        ),
        "_handoff": {
            "from": "architect",
            "to": "pm",
            "direction": "forward",
            "reason": "Align assignment scope (UI/UX vs backend vs CLI, etc.)",
        },
    }


def pm_scope_node(state: OfficeState) -> dict:
    turns = len(_scope_dialogue(state))
    force_lock = turns >= max(1, MAX_SCOPE_DIALOGUE_TURNS - 1)
    last_arch = state.get("architecture_brief") or {}
    prior = state.get("scope_agreement") or {}
    architect_agrees = bool(state.get("architect_agrees", True))
    agreement = run_pm_scope_alignment(
        state["task"],
        last_arch,
        state.get("brief_answers") or "",
        state.get("brief_assumptions") or [],
        dialogue=state.get("dialogue") or [],
        scope_agreement=prior if prior else None,
        architect_agrees=architect_agrees,
        force_lock=force_lock,
    )
    _remember_notes(state, "pm", agreement)
    pm_msg = agreement.get("architect_response") or ""
    dlg = _append_scope_dialogue(state, "pm", "architect", pm_msg)
    merged_state = {**state, **dlg}
    locked = bool(agreement.get("scope_locked")) or force_lock
    if force_lock and not agreement.get("scope_locked"):
        agreement = {**agreement, "scope_locked": True}
        risks = list(agreement.get("risks") or [])
        risks.append("Scope locked at turn limit; PM proceeded with best-effort alignment.")
        agreement["risks"] = risks
    ptype = agreement.get("project_type") or "mixed"
    needs_design = bool(agreement.get("needs_designer"))
    track = "Designer + build" if needs_design else "Build without UX track"
    resolved = bool(agreement.get("scope_resolved", True))

    if locked:
        update_task_board(state["thread_id"], state["task"], "planning", "pm")
        return {
            "scope_agreement": agreement,
            "scope_locked": True,
            "current_agent": "pm",
            "status": "planning",
            **dlg,
            **_step(
                merged_state,
                f"Scope locked — {ptype} ({track}). PM drafting the plan.",
                kind="handoff",
                from_agent="pm",
                to_agent="pm",
                direction="forward",
            ),
        }

    update_task_board(state["thread_id"], state["task"], "scoping", "architect")
    reason = "Architect must confirm PM's adjustment" if not resolved else "Scope huddle continues"
    return {
        "scope_agreement": agreement,
        "scope_locked": False,
        "current_agent": "pm",
        "status": "scoping",
        **dlg,
        **_step(
            merged_state,
            f"PM proposed scope ({ptype}); {reason}.",
            kind="handoff",
            from_agent="pm",
            to_agent="architect",
            direction="return" if not resolved else "forward",
        ),
        "_handoff": {
            "from": "pm",
            "to": "architect",
            "direction": "return" if not resolved else "forward",
            "reason": reason,
        },
    }


def pm_node(state: OfficeState) -> dict:
    parts: list[str] = []
    if state.get("brief_answers"):
        parts.append(f"Human clarifications before planning:\n{state['brief_answers']}")
    if state.get("feedback"):
        parts.append(state["feedback"])
    from_agent = state.get("escalation_from")
    release_triage = _is_release_rejection_triage(state)
    if from_agent:
        parts.append(f"Downstream agent ({from_agent}) reported a scope problem. Revise the plan.")
    if release_triage:
        parts.append(
            "Supervisor rejected release. Triage with the team: update acceptance criteria if needed, "
            "then route fixes through build and QA again — do not ask for a new plan gate."
        )
    feedback = "\n\n".join(parts)
    plan: dict[str, Any] = {}
    for attempt in range(2):
        try:
            plan = run_pm(
                state["task"],
                feedback,
                architecture_brief=state.get("architecture_brief") or None,
                scope_agreement=state.get("scope_agreement") or None,
            )
            break
        except RuntimeError as exc:
            if attempt == 0 and "Could not parse model JSON" in str(exc):
                feedback = (
                    f"{feedback}\n\n[System] Your last response was invalid JSON. "
                    "Return smaller, complete JSON for the plan."
                ).strip()
                _step(
                    state,
                    "PM JSON parse failed — retrying with a shorter plan request.",
                    kind="work",
                    from_agent="pm",
                )
                continue
            raise
    _remember_notes(state, "pm", plan)
    if release_triage:
        return_to = _pm_return_after_release(state)
        status = {"designer": "designing", "developer": "implementing"}[return_to]
        handoff_feedback = (state.get("feedback") or "").strip()
        update_task_board(state["thread_id"], state["task"], status, "pm")
        return {
            "plan": plan,
            "plan_approved": True,
            "skip_plan_approval": True,
            "return_to_after_pm": return_to,
            "release_triage": False,
            "ac_verified": False,
            "qa_passed": False,
            "feedback": handoff_feedback if return_to == "developer" else "",
            "current_agent": "pm",
            "status": status,
            "escalation": None,
            "escalation_from": None,
            "continue_run": False,
            **_step(
                state,
                f"PM triaged release rejection — next: {return_to} (no plan gate).",
                kind="handoff",
                from_agent="pm",
                to_agent=return_to,
                direction="forward",
            ),
            "_handoff": {"from": "pm", "to": return_to, "direction": "forward", "reason": "Release rejection triage"},
        }
    downstream = from_agent in ("designer", "developer", "qa")
    if downstream:
        return_to = "developer" if from_agent == "qa" else from_agent
        if from_agent == "qa":
            return_to = _pm_return_after_qa(state)
        status = {"designer": "designing", "developer": "implementing", "qa": "testing"}[return_to]
        update_task_board(state["thread_id"], state["task"], status, "pm")
        return {
            "plan": plan,
            "plan_approved": True,
            "skip_plan_approval": True,
            "return_to_after_pm": return_to,
            "current_agent": "pm",
            "status": status,
            "feedback": "",
            "escalation": None,
            "escalation_from": None,
            **_step(
                state,
                f"PM adjusted the plan after {from_agent} feedback — next: {return_to} (no plan gate).",
                kind="handoff",
                from_agent="pm",
                to_agent=return_to,
                direction="forward",
            ),
            "_handoff": {"from": "pm", "to": return_to, "direction": "forward"},
        }
    update_task_board(state["thread_id"], state["task"], "awaiting_plan_approval", "pm")
    plan_text = (
        "PM produced a plan."
        if not from_agent
        else f"PM revised the plan after scope feedback from {from_agent}."
    )
    return {
        "plan": plan,
        "plan_approved": False,
        "skip_plan_approval": False,
        "return_to_after_pm": "",
        "current_agent": "pm",
        "status": "awaiting_plan_approval",
        "escalation": None,
        "escalation_from": None,
        **_step(
            state,
            plan_text,
            kind="handoff",
            from_agent="pm",
            to_agent="human",
            direction="forward",
        ),
        "_handoff": {"from": "pm", "to": "human", "direction": "forward"},
    }


def approve_plan_node(state: OfficeState) -> dict:
    plan = state.get("plan") or {}
    decision = interrupt(
        {
            "gate": "plan",
            "prompt": "Meet with the PM in the meeting room. Verify acceptance criteria are complete and testable, then sign off to start design and build.",
            "plan": plan,
            "acceptance_criteria": plan.get("acceptance_criteria") or [],
            "scope_agreement": state.get("scope_agreement") or {},
            "architecture_brief": state.get("architecture_brief") or {},
        }
    )
    approved = bool(decision.get("approved")) if isinstance(decision, dict) else False
    feedback = decision.get("feedback", "") if isinstance(decision, dict) else str(decision)
    if approved:
        if needs_designer_track(state):
            update_task_board(state["thread_id"], state["task"], "designing", "designer")
            return {
                "plan_approved": True,
                "feedback": "",
                "escalation": None,
                "status": "designing",
                **_step(
                    state,
                    "Supervisor signed off acceptance criteria — plan approved.",
                    kind="gate",
                    from_agent="human",
                    to_agent="designer",
                    direction="forward",
                ),
                "_handoff": {
                    "from": "human",
                    "to": "designer",
                    "direction": "forward",
                    "reason": "AC signed off — design track starts",
                },
            }
        update_task_board(state["thread_id"], state["task"], "implementing", "developer")
        return {
            "plan_approved": True,
            "design_spec": minimal_design_spec(state),
            "feedback": "",
            "escalation": None,
            "status": "implementing",
            **_step(
                state,
                "Supervisor signed off AC — no UI/UX track; straight to Developer.",
                kind="gate",
                from_agent="human",
                to_agent="developer",
                direction="forward",
            ),
            "_handoff": {
                "from": "human",
                "to": "developer",
                "direction": "forward",
                "reason": "AC signed off — build starts",
            },
        }
    note = feedback or "Revise the plan."
    _remember(state, "pm", "mistake", f"Plan was rejected: {note}")
    return {
        "plan_approved": False,
        "feedback": note,
        "status": "revising",
        **_step(
            state,
            f"Supervisor sent plan back — AC or scope needs changes: {feedback}",
            kind="gate",
            from_agent="human",
            to_agent="pm",
            direction="return",
        ),
        "_handoff": {
            "from": "human",
            "to": "pm",
            "direction": "return",
            "reason": note[:120],
        },
    }


def designer_node(state: OfficeState) -> dict:
    plan = state.get("plan") or {}
    spec = run_designer(state["task"], plan, state.get("feedback") or "")
    _remember_notes(state, "designer", spec)
    esc = _parse_escalation(spec)
    if esc and esc["target"] == "pm" and designer_escalation_is_no_ui_mismatch(esc, plan):
        _remember(
            state,
            "designer",
            "context",
            "Non-UI plan: documented console/CLI behavior instead of escalating to PM.",
        )
        spec = {
            **spec,
            "scope_ok": True,
            "escalation": None,
            "product_intent": spec.get("product_intent")
            or "Deliverable is non-UI (console/CLI/files). Developer implements behavior per PM acceptance criteria.",
            "screens": spec.get("screens") or ["Console output (stdout/stderr)"],
            "user_flows": spec.get("user_flows")
            or ["User runs the program from a terminal and reads printed output."],
        }
        esc = None
    if esc and esc["target"] == "pm" and not _scope_limit_reached(state):
        update_task_board(state["thread_id"], state["task"], "revising", "designer")
        reason = esc["reason"][:120]
        return {
            **_escalation_update(state, "designer", esc),
            "design_spec": spec,
            "current_agent": "designer",
            "status": "revising",
            **_step(
                state,
                f"Designer sent scope back to PM: {reason}",
                kind="handoff",
                from_agent="designer",
                to_agent="pm",
                direction="return",
            ),
        }
    update_task_board(state["thread_id"], state["task"], "implementing", "developer")
    return {
        "design_spec": spec,
        "current_agent": "designer",
        "status": "implementing",
        "feedback": "",
        "escalation": None,
        "escalation_from": None,
        **_step(
            state,
            "Designer produced a spec.",
            kind="handoff",
            from_agent="designer",
            to_agent="developer",
            direction="forward",
        ),
        "_handoff": {"from": "designer", "to": "developer", "direction": "forward"},
    }


def developer_node(state: OfficeState) -> dict:
    feedback = state.get("feedback") or ""
    result: dict | None = None
    for attempt in range(2):
        try:
            result = run_developer(
                state["thread_id"],
                state["task"],
                state.get("plan") or {},
                state.get("design_spec") or {},
                feedback,
            )
            break
        except RuntimeError as exc:
            if attempt == 0 and "Could not parse model JSON" in str(exc):
                feedback = (
                    f"{feedback}\n\n[System] Your last response was invalid or truncated JSON. "
                    "Return complete JSON with smaller files[] bodies; stay on the plan's stack."
                ).strip()
                _step(
                    state,
                    "Developer JSON parse failed — retrying with a shorter output request.",
                    kind="work",
                    from_agent="developer",
                )
                continue
            raise
    if result is None:
        raise RuntimeError("Developer produced no result")
    _remember_notes(state, "developer", result)
    esc = _parse_escalation(result)
    if esc and esc["target"] in ("pm", "designer") and not _scope_limit_reached(state):
        status = "revising" if esc["target"] == "pm" else "designing"
        update_task_board(state["thread_id"], state["task"], status, "developer")
        target = esc["target"]
        reason = esc["reason"][:120]
        return {
            **_escalation_update(state, "developer", esc),
            "implementation_summary": result.get("summary") or esc["reason"],
            "current_agent": "developer",
            "status": status,
            **_step(
                state,
                f"Developer sent scope back to {target}: {reason}",
                kind="handoff",
                from_agent="developer",
                to_agent=target,
                direction="return",
            ),
        }
    update_task_board(state["thread_id"], state["task"], "testing", "qa")
    return {
        "implementation_summary": result["summary"],
        "files_written": result.get("written") or [item["path"] for item in result.get("files", [])],
        "current_agent": "developer",
        "status": "testing",
        "feedback": "",
        "escalation": None,
        "escalation_from": None,
        **_step(
            state,
            f"Developer wrote {len(result.get('files') or [])} file(s).",
            kind="handoff",
            from_agent="developer",
            to_agent="qa",
            direction="forward",
        ),
        "_handoff": {"from": "developer", "to": "qa", "direction": "forward"},
    }


def qa_node(state: OfficeState) -> dict:
    report = run_qa(
        state["thread_id"],
        state["task"],
        state.get("plan") or {},
        state.get("design_spec") or {},
        state.get("implementation_summary") or "",
    )
    report = enrich_qa_report(state["thread_id"], report)
    emit(
        {
            "type": "qa_validation",
            "runs": report.get("validation_runs") or [],
            "passed": report.get("passed"),
        }
    )
    _remember_notes(state, "qa", report)
    esc = _parse_escalation(report)
    if not esc:
        assessment = report.get("validation_assessment") or {}
        if assessment.get("kind") not in (None, "ok") and assessment.get("escalate_to") == "pm":
            if not _scope_limit_reached(state):
                esc = {
                    "target": "pm",
                    "reason": assessment.get("reason") or "QA could not run required validations.",
                }
    if esc and not _scope_limit_reached(state):
        status = {"pm": "revising", "designer": "designing", "developer": "implementing"}[esc["target"]]
        update_task_board(state["thread_id"], state["task"], status, "qa")
        target = esc["target"]
        reason = esc["reason"][:120]
        return {
            **_escalation_update(state, "qa", esc),
            "test_results": report,
            "qa_passed": False,
            "current_agent": "qa",
            "status": status,
            **_step(
                state,
                f"QA sent scope back to {target}: {reason}",
                kind="handoff",
                from_agent="qa",
                to_agent=target,
                direction="return",
            ),
        }

    passed = bool(report.get("passed"))
    retry_count = int(state.get("retry_count") or 0)
    if not passed:
        retry_count += 1
        findings = report.get("findings") or []
        feedback = "\n".join(
            f"- [{item.get('severity')}] {item.get('title')}: {item.get('detail')}" for item in findings
        ) or report.get("summary", "QA found issues.")
        assessment = report.get("validation_assessment") or {}
        pm_triage = (
            retry_count >= MAX_QA_RETRIES
            and assessment.get("escalate_to") == "pm"
            and not _scope_limit_reached(state)
        )
        status = (
            "revising"
            if pm_triage
            else ("awaiting_release" if retry_count >= MAX_QA_RETRIES else "implementing")
        )
        _remember(state, "qa", "mistake", feedback or "QA failed the build.")
        _remember(state, "developer", "mistake", f"QA sent this back: {feedback or 'fix the findings.'}")
        update_task_board(state["thread_id"], state["task"], status, "qa")
        handoff = None
        if retry_count < MAX_QA_RETRIES:
            handoff = {
                "from": "qa",
                "to": "developer",
                "direction": "return",
                "reason": "QA found defects to fix",
            }
        qa_fail = f"QA failed (retry {retry_count}/{MAX_QA_RETRIES})."
        triage: dict[str, Any] = {}
        if pm_triage:
            triage["escalation_from"] = "qa"
            triage["feedback"] = (
                f"{feedback}\n\n[Validation triage for PM]\n{assessment.get('reason', '')}".strip()
            )
        return {
            "test_results": report,
            "qa_passed": False,
            "retry_count": retry_count,
            "feedback": triage.get("feedback", feedback),
            "current_agent": "qa",
            "status": status,
            "escalation": None,
            **triage,
            **_step(
                state,
                qa_fail,
                kind="handoff" if handoff else "work",
                from_agent="qa" if handoff else "qa",
                to_agent="developer" if handoff else "",
                direction="return" if handoff else "",
            ),
            **({"_handoff": handoff} if handoff else {}),
        }
    update_task_board(state["thread_id"], state["task"], "verifying_ac", "pm")
    qa_pass = "QA passed" + (
        f" ({len(report.get('validation_runs') or [])} validation run(s))."
        if report.get("validation_runs")
        else "."
    )
    return {
        "test_results": report,
        "qa_passed": True,
        "ac_verified": False,
        "current_agent": "qa",
        "status": "verifying_ac",
        "escalation": None,
        **_step(
            state,
            qa_pass + " PM will verify all acceptance criteria against QA evidence.",
            kind="handoff",
            from_agent="qa",
            to_agent="pm",
            direction="forward",
        ),
        "_handoff": {
            "from": "qa",
            "to": "pm",
            "direction": "forward",
            "reason": "Hand off test results and verification for PM AC review",
        },
    }


def pm_ac_verify_node(state: OfficeState) -> dict:
    verification = run_pm_ac_verification(
        state["task"],
        state.get("plan") or {},
        state.get("test_results") or {},
        state.get("implementation_summary") or "",
    )
    _remember_notes(state, "pm", verification)
    all_met = bool(verification.get("all_ac_met"))
    gaps = verification.get("gaps") or []
    summary = verification.get("summary") or ""
    if all_met:
        update_task_board(state["thread_id"], state["task"], "awaiting_release", "human")
        return {
            "ac_verification": verification,
            "ac_verified": True,
            "current_agent": "pm",
            "status": "awaiting_release",
            "feedback": "",
            **_step(
                state,
                "PM confirmed all acceptance criteria are met per QA test results — ready for supervisor release.",
                kind="handoff",
                from_agent="pm",
                to_agent="human",
                direction="forward",
            ),
            "_handoff": {"from": "pm", "to": "human", "direction": "forward"},
        }
    return_to = verification.get("return_to") or "developer"
    gap_text = "\n".join(f"- {g}" for g in gaps) if gaps else summary
    feedback = f"[PM AC review after QA]\n{gap_text}"
    _remember(state, "pm", "context", f"AC not ready for release: {summary[:200]}")
    if return_to == "qa":
        _remember(state, "qa", "context", feedback[:300])
        update_task_board(state["thread_id"], state["task"], "testing", "qa")
        next_agent = "qa"
        reason = "PM asked QA to re-run tests with updated evidence expectations"
    else:
        _remember(state, "developer", "mistake", feedback[:300])
        update_task_board(state["thread_id"], state["task"], "implementing", "developer")
        next_agent = "developer"
        reason = "Acceptance criteria not fully met per QA evidence"
    return {
        "ac_verification": verification,
        "ac_verified": False,
        "feedback": feedback if return_to == "developer" else "",
        "current_agent": "pm",
        "status": "testing" if return_to == "qa" else "implementing",
        **_step(
            state,
            f"PM: not all AC met per QA evidence — {summary[:120]}",
            kind="handoff",
            from_agent="pm",
            to_agent=next_agent,
            direction="return",
        ),
        "_handoff": {
            "from": "pm",
            "to": next_agent,
            "direction": "return",
            "reason": reason,
        },
    }


def review_node(state: OfficeState) -> dict:
    plan = state.get("plan") or {}
    decision = interrupt(
        {
            "gate": "release",
            "prompt": "QA passed and the PM confirmed every acceptance criterion is met. Approve release?",
            "qa_passed": state.get("qa_passed"),
            "ac_verified": state.get("ac_verified"),
            "acceptance_criteria": plan.get("acceptance_criteria") or [],
            "test_results": state.get("test_results") or {},
            "ac_verification": state.get("ac_verification") or {},
            "files_written": state.get("files_written") or [],
            "implementation_summary": state.get("implementation_summary") or "",
        }
    )
    approved = bool(decision.get("approved")) if isinstance(decision, dict) else False
    feedback = decision.get("feedback", "") if isinstance(decision, dict) else str(decision)
    if approved:
        task = (state.get("task") or "").strip()
        if task:
            _remember(state, "pm", "context", f"Released slice: {task[:180]}")
        update_task_board(state["thread_id"], state["task"], "released", "human")
        return {
            "release_approved": True,
            "status": "released",
            **_step(
                state,
                "Human approved release.",
                kind="gate",
                from_agent="human",
                to_agent="human",
                direction="forward",
            ),
        }
    release_rejection_count = int(state.get("release_rejection_count") or 0) + 1
    blocked = release_rejection_count >= MAX_QA_RETRIES
    note = feedback or "Revise scope, acceptance criteria, or implementation."
    pm_feedback = f"[Human rejected release]\n{note}"
    _remember(state, "pm", "mistake", f"Release rejected by supervisor: {note[:200]}")
    _remember(state, "developer", "context", f"Supervisor rejected release (PM triaging): {note[:200]}")
    update_task_board(
        state["thread_id"],
        state["task"],
        "blocked" if blocked else "revising",
        "pm" if not blocked else "human",
    )
    handoff = None
    if not blocked:
        handoff = {
            "from": "human",
            "to": "pm",
            "direction": "return",
            "reason": note,
        }
    return {
        "release_approved": False,
        "release_rejection_count": release_rejection_count,
        "release_triage": not blocked,
        "ac_verified": False,
        "qa_passed": False,
        "escalation_from": "release",
        "skip_plan_approval": False,
        "return_to_after_pm": "",
        "feedback": pm_feedback,
        "status": "blocked" if blocked else "revising",
        **_step(
            state,
            f"Human rejected release — PM will triage with the team: {note[:120]}",
            kind="handoff" if handoff else "gate",
            from_agent="human",
            to_agent="pm" if handoff else "",
            direction="return" if handoff else "",
        ),
        **({"_handoff": handoff} if handoff else {}),
    }


def after_pm_scope(state: OfficeState) -> Literal["architect", "pm"]:
    return "pm" if state.get("scope_locked") else "architect"


def after_start(state: OfficeState) -> Literal["pm_discover", "pm"]:
    if state.get("continue_run") and state.get("plan"):
        return "pm"
    return "pm_discover"


def after_discover(state: OfficeState) -> Literal["confirm_brief", "architect"]:
    if state.get("brief_questions"):
        return "confirm_brief"
    return "architect"


def after_pm(state: OfficeState) -> Literal["approve_plan", "designer", "developer", "qa"]:
    target = state.get("return_to_after_pm") or ""
    if state.get("skip_plan_approval") and target in ("designer", "developer", "qa"):
        return target
    return "approve_plan"


def after_plan(state: OfficeState) -> Literal["designer", "developer", "pm"]:
    if not state.get("plan_approved"):
        return "pm"
    if needs_designer_track(state):
        return "designer"
    return "developer"


def after_designer(state: OfficeState) -> Literal["developer", "pm"]:
    esc = state.get("escalation") or {}
    if esc.get("target") == "pm":
        return "pm"
    return "developer"


def after_developer(state: OfficeState) -> Literal["qa", "pm", "designer"]:
    esc = state.get("escalation") or {}
    target = esc.get("target")
    if target == "pm":
        return "pm"
    if target == "designer":
        return "designer"
    return "qa"


def after_qa(state: OfficeState) -> Literal["developer", "pm_ac_verify", "review", "pm", "designer"]:
    esc = state.get("escalation") or {}
    target = esc.get("target")
    if target in ("pm", "designer", "developer"):
        return target
    if state.get("qa_passed"):
        return "pm_ac_verify"
    if int(state.get("retry_count") or 0) >= MAX_QA_RETRIES:
        assessment = (state.get("test_results") or {}).get("validation_assessment") or {}
        if assessment.get("escalate_to") == "pm" and not _scope_limit_reached(state):
            return "pm"
        return "review"
    return "developer"


def after_pm_ac_verify(state: OfficeState) -> Literal["developer", "qa", "review"]:
    if state.get("ac_verified"):
        return "review"
    ac = state.get("ac_verification") or {}
    if ac.get("return_to") == "qa":
        return "qa"
    return "developer"


def after_review(state: OfficeState) -> Literal["pm", "__end__"]:
    if state.get("release_approved") or state.get("status") == "blocked":
        return END
    return "pm"


def _bind_thread(state: OfficeState) -> None:
    if state.get("thread_id"):
        thread_id_var.set(state["thread_id"])


def wrap_agent(name: str, fn):
    def wrapped(state: OfficeState) -> dict:
        _bind_thread(state)
        token = agent_var.set(name)
        emit({"type": "agent_started", "agent": name})
        try:
            result = fn(state) or {}
            handoff = result.pop("_handoff", None)
            if handoff:
                emit({"type": "handoff", **handoff})
            emit({"type": "agent_finished", "agent": name, "status": result.get("status")})
            return result
        except Exception as exc:  # noqa: BLE001
            emit({"type": "error", "agent": name, "message": str(exc)})
            raise
        finally:
            agent_var.reset(token)

    return wrapped


def wrap_gate(name: str, fn):
    def wrapped(state: OfficeState) -> dict:
        _bind_thread(state)
        result = fn(state) or {}
        handoff = result.pop("_handoff", None)
        if handoff:
            emit({"type": "handoff", **handoff})
        return result

    return wrapped


def compile_graph(checkpointer: SqliteSaver | None = None):
    builder = StateGraph(OfficeState)
    builder.add_node("pm_discover", wrap_agent("pm", pm_discover_node))
    builder.add_node("confirm_brief", wrap_gate("brief", confirm_brief_node))
    builder.add_node("architect", wrap_agent("architect", architect_node))
    builder.add_node("pm_scope", wrap_agent("pm", pm_scope_node))
    builder.add_node("pm", wrap_agent("pm", pm_node))
    builder.add_node("approve_plan", wrap_gate("plan", approve_plan_node))
    builder.add_node("designer", wrap_agent("designer", designer_node))
    builder.add_node("developer", wrap_agent("developer", developer_node))
    builder.add_node("qa", wrap_agent("qa", qa_node))
    builder.add_node("pm_ac_verify", wrap_agent("pm", pm_ac_verify_node))
    builder.add_node("review", wrap_gate("release", review_node))

    builder.add_conditional_edges(
        START,
        after_start,
        {"pm_discover": "pm_discover", "pm": "pm"},
    )
    builder.add_conditional_edges(
        "pm_discover",
        after_discover,
        {"confirm_brief": "confirm_brief", "architect": "architect"},
    )
    builder.add_edge("confirm_brief", "architect")
    builder.add_edge("architect", "pm_scope")
    builder.add_conditional_edges(
        "pm_scope",
        after_pm_scope,
        {"architect": "architect", "pm": "pm"},
    )
    builder.add_conditional_edges(
        "pm",
        after_pm,
        {
            "approve_plan": "approve_plan",
            "designer": "designer",
            "developer": "developer",
            "qa": "qa",
        },
    )
    builder.add_conditional_edges(
        "approve_plan",
        after_plan,
        {"designer": "designer", "developer": "developer", "pm": "pm"},
    )
    builder.add_conditional_edges(
        "designer",
        after_designer,
        {"developer": "developer", "pm": "pm"},
    )
    builder.add_conditional_edges(
        "developer",
        after_developer,
        {"qa": "qa", "pm": "pm", "designer": "designer"},
    )
    builder.add_conditional_edges(
        "qa",
        after_qa,
        {
            "developer": "developer",
            "pm_ac_verify": "pm_ac_verify",
            "review": "review",
            "pm": "pm",
            "designer": "designer",
        },
    )
    builder.add_conditional_edges(
        "pm_ac_verify",
        after_pm_ac_verify,
        {"developer": "developer", "qa": "qa", "review": "review"},
    )
    builder.add_conditional_edges("review", after_review, {"pm": "pm", END: END})
    return builder.compile(checkpointer=checkpointer)


def make_checkpointer() -> SqliteSaver:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return SqliteSaver.from_conn_string(str(CHECKPOINT_DB))
