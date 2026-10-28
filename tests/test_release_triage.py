"""Release rejection must resume PM → build → QA without a second plan gate."""

from unittest.mock import patch

from graph import after_pm, pm_node, review_node


def _release_state() -> dict:
    return {
        "task": "Smoke",
        "thread_id": "rel000000001",
        "history": [],
        "activity": [],
        "plan": {"goal": "g", "acceptance_criteria": ["AC1"]},
        "plan_approved": True,
        "qa_passed": True,
        "ac_verified": True,
        "scope_agreement": {"needs_designer": False},
    }


@patch("graph.interrupt", return_value={"approved": False, "feedback": "Fix the button"})
@patch("graph.update_task_board")
def test_release_reject_sets_triage(_board, _interrupt):
    out = review_node(_release_state())
    assert out.get("release_triage") is True
    assert out.get("qa_passed") is False
    assert "plan_approved" not in out or out.get("plan_approved") is not False


@patch("graph.update_task_board")
@patch("graph._remember_notes")
@patch("graph._step", return_value={"history": [], "activity": []})
@patch("graph.run_pm", return_value={"goal": "g", "acceptance_criteria": ["AC1 fixed"]})
def test_pm_release_triage_routes_developer_for_layout_note(_run_pm, _step, _notes, _board):
    state = {
        **_release_state(),
        "feedback": "[Human rejected release]\nFix the layout",
        "release_triage": True,
        "escalation_from": "release",
    }
    out = pm_node(state)
    assert out.get("return_to_after_pm") == "developer"


@patch("graph.update_task_board")
@patch("graph._remember_notes")
@patch("graph._step", return_value={"history": [], "activity": []})
@patch("graph.run_pm", return_value={"goal": "g", "acceptance_criteria": ["AC1 fixed"]})
def test_pm_release_triage_skips_plan_gate(_run_pm, _step, _notes, _board):
    state = {
        **_release_state(),
        "feedback": "[Human rejected release]\nFix the button",
        "release_triage": True,
    }
    out = pm_node(state)
    assert out.get("skip_plan_approval") is True
    assert out.get("return_to_after_pm") == "developer"
    assert out.get("release_triage") is False
    merged = {**state, **out}
    assert after_pm(merged) == "developer"
