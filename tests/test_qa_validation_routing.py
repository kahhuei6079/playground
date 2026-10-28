"""QA validation assessment and PM return routing."""

from graph import _pm_return_after_qa, _qa_retry_feedback, after_pm_ac_verify, after_qa
from qa_runner import assess_validation_coverage


def test_assess_blocked_commands_escalates_pm(tmp_path, monkeypatch):
    from memory import workspace_for

    def fake_workspace(_tid: str):
        return tmp_path

    monkeypatch.setattr("qa_runner.workspace_for", fake_workspace)
    report = {
        "validation_runs": [],
        "tests_to_execute": ["python -m pytest -q"],
        "test_matrix": [{"criterion": "x", "method": "auto"}],
        "findings": [],
    }
    out = assess_validation_coverage("t1", report)
    assert out["kind"] == "blocked_commands"
    assert out["escalate_to"] == "pm"


def test_pm_return_after_qa_sends_developer_for_validation_gap():
    state = {
        "test_results": {
            "validation_assessment": {
                "kind": "not_executed",
                "escalate_to": "developer",
                "reason": "no runs",
            }
        }
    }
    assert _pm_return_after_qa(state) == "developer"


def test_after_qa_pm_triage_before_human():
    state = {
        "qa_passed": False,
        "retry_count": 2,
        "test_results": {"validation_assessment": {"escalate_to": "pm", "kind": "blocked_commands"}},
        "scope_escalation_count": 0,
    }
    assert after_qa(state) == "pm"


def test_after_pm_ac_verify_can_return_qa():
    state = {"ac_verified": False, "ac_verification": {"return_to": "qa"}}
    assert after_pm_ac_verify(state) == "qa"


def test_qa_retry_feedback_prioritizes_actual_validation_output():
    feedback = _qa_retry_feedback(
        {
            "validation_runs": [
                {
                    "command": "node tests/unit/test_scroll_logic.js",
                    "exit_code": 1,
                    "passed": False,
                    "stderr": "AssertionError: expected null, got scroll options",
                }
            ],
            "findings": [
                {
                    "severity": "high",
                    "title": "Node DOM limitation",
                    "detail": "The environment may not support browser APIs.",
                }
            ],
        }
    )
    assert feedback.index("AssertionError: expected null") < feedback.index("Node DOM limitation")
