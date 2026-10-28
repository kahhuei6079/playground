from graph import after_start
from runtime import _task_title_for_thread


def test_after_start_continue_with_plan():
    assert after_start({"continue_run": True, "plan": {"goal": "x"}}) == "pm"
    assert after_start({"continue_run": True}) == "pm_discover"
    assert after_start({}) == "pm_discover"


def test_task_title_from_board():
    title = _task_title_for_thread("t", {"values": {}})
    assert title == "test"
