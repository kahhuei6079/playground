"""Gate nodes must emit _handoff payloads — the UI animates these via SSE handoff events."""

from unittest.mock import patch

from graph import approve_plan_node, confirm_brief_node


def _base_state() -> dict:
    return {
        "task": "Smoke task",
        "thread_id": "smoke0000001",
        "history": [],
        "activity": [],
        "plan": {
            "goal": "g",
            "acceptance_criteria": ["AC1"],
            "requirements": [],
            "scope": "s",
        },
    }


@patch("graph.interrupt", return_value={"approved": True, "feedback": "Answers"})
def test_confirm_brief_handoff_to_architect(_interrupt):
    out = confirm_brief_node(_base_state())
    assert out["_handoff"] == {
        "from": "human",
        "to": "architect",
        "direction": "forward",
        "reason": "Brief confirmed — Architect opens scope",
    }


@patch("graph.interrupt", return_value={"approved": True, "feedback": ""})
@patch("graph.needs_designer_track", return_value=True)
@patch("graph.update_task_board")
def test_approve_plan_handoff_to_designer(_board, _designer, _interrupt):
    out = approve_plan_node(_base_state())
    assert out["_handoff"]["from"] == "human"
    assert out["_handoff"]["to"] == "designer"
    assert out["_handoff"]["direction"] == "forward"


@patch("graph.interrupt", return_value={"approved": True, "feedback": ""})
@patch("graph.needs_designer_track", return_value=False)
@patch("graph.minimal_design_spec", return_value={})
@patch("graph.update_task_board")
def test_approve_plan_handoff_to_developer(_board, _spec, _designer, _interrupt):
    out = approve_plan_node(_base_state())
    assert out["_handoff"]["to"] == "developer"


@patch("graph.interrupt", return_value={"approved": False, "feedback": "Fix AC3"})
@patch("graph.update_task_board")
def test_approve_plan_reject_handoff_to_pm(_board, _interrupt):
    out = approve_plan_node(_base_state())
    assert out["_handoff"]["from"] == "human"
    assert out["_handoff"]["to"] == "pm"
    assert out["_handoff"]["direction"] == "return"
