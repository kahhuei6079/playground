"""After a gate resume, pending nodes (e.g. pm) must still run."""

from unittest.mock import patch

from langgraph.types import Command
from graph import compile_graph, make_checkpointer


def test_release_reject_drains_into_pm_node():
    tid = "drainrelease01"
    config = {"configurable": {"thread_id": tid}}
    with make_checkpointer() as cp:
        g = compile_graph(cp)
        g.update_state(
            config,
            {
                "task": "drain test",
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
                "release_rejection_count": 0,
                "scope_agreement": {"needs_designer": False},
            },
            as_node="pm_ac_verify",
        )
        list(g.stream(None, config, stream_mode="updates"))

    from runtime import _execute

    with patch("graph.run_pm", return_value={"goal": "g", "acceptance_criteria": ["AC1"]}):
        with patch("graph.run_developer", return_value={"summary": "s", "files": [], "written": []}):
            with patch("graph.run_qa", return_value={"passed": True, "summary": "ok", "scope_ok": True}):
                with patch("graph.enrich_qa_report", side_effect=lambda _t, r: r):
                    with patch(
                        "graph.run_pm_ac_verification",
                        return_value={"all_ac_met": True, "summary": "ok"},
                    ):
                        _execute(
                            tid,
                            Command(resume={"approved": False, "feedback": "send to pm"}),
                        )
    with make_checkpointer() as cp:
        g = compile_graph(cp)
        st = g.get_state(config)
        assert st.values.get("current_agent") != "review"
        assert list(st.next or []) != ["pm"] or st.values.get("skip_plan_approval")
