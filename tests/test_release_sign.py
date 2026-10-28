"""Sign release must work in one /api/decide when review is pending but interrupt not materialized."""

import time

from graph import compile_graph, make_checkpointer
from runtime import is_busy, resume_task, snapshot


def _seed_pending_release(tid: str) -> None:
    config = {"configurable": {"thread_id": tid}}
    with make_checkpointer() as cp:
        g = compile_graph(cp)
        g.update_state(
            config,
            {
                "task": "one-click release",
                "thread_id": tid,
                "status": "awaiting_release",
                "qa_passed": True,
                "ac_verified": True,
                "plan": {"goal": "g", "acceptance_criteria": ["AC1"]},
                "test_results": {"passed": True, "summary": "ok"},
                "ac_verification": {"all_ac_met": True, "summary": "ok", "coverage": []},
                "history": [],
                "activity": [],
                "dialogue": [],
                "scope_agreement": {"needs_designer": False},
            },
            as_node="pm_ac_verify",
        )


def test_release_sign_one_decide_when_review_pending():
    tid = "release_one_click01"
    _seed_pending_release(tid)
    snap = snapshot(tid)
    assert snap.get("interrupt") is None
    assert "review" in (snap.get("next") or [])

    resume_task(tid, True, "")
    for _ in range(200):
        if not is_busy(tid):
            break
        time.sleep(0.02)

    final = snapshot(tid)
    assert final["values"].get("status") == "released"
    assert final.get("interrupt") is None
