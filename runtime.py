from __future__ import annotations

import threading
import uuid
from typing import Any, Literal

from langgraph.types import Command

from events import emit, hub, thread_id_var
from graph import compile_graph, make_checkpointer
from memory import list_tasks, update_task_board

_run_lock = threading.Lock()
_MAX_GRAPH_DRAIN_STEPS = 48
_RELEASE_CHAIN_KEY = "__release_chain__"
_active: set[str] = set()
_active_lock = threading.Lock()


def _interrupt_payload(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return None
    first = interrupts[0]
    return getattr(first, "value", first)


def _interrupt_from_state(state) -> dict | None:
    for task in state.tasks or []:
        interrupts = getattr(task, "interrupts", None) or ()
        if interrupts:
            return getattr(interrupts[0], "value", interrupts[0])
    return None


def _checkpoint_view(thread_id: str) -> dict[str, Any]:
    with make_checkpointer() as checkpointer:
        graph = compile_graph(checkpointer)
        state = graph.get_state({"configurable": {"thread_id": thread_id}})
    values = dict(state.values or {})
    interrupt = _interrupt_from_state(state)
    return {
        "exists": bool(state.values),
        "next": list(state.next or []),
        "values": values,
        "interrupt": interrupt,
    }


def snapshot(thread_id: str) -> dict[str, Any]:
    live = hub.snapshot(thread_id)
    ckpt = _checkpoint_view(thread_id)
    return {
        "thread_id": thread_id,
        "exists": ckpt["exists"],
        "next": ckpt["next"],
        "values": ckpt["values"] if ckpt["exists"] else {"task": live.get("task"), "status": live.get("status")},
        "interrupt": ckpt["interrupt"],
        "live": live,
        "pending_nodes": ckpt["next"],
    }


def _emit_chunk_updates(thread_id: str, result: dict[str, Any]) -> None:
    if not isinstance(result, dict):
        return
    for node_name, update in result.items():
        if node_name.startswith("__"):
            continue
        emit({"type": "state_update", "node": node_name, "update": _public(update)})


def _stream_until_pause(
    thread_id: str,
    graph,
    config: dict[str, Any],
    inbound: dict | Command | None,
) -> Literal["interrupt", "cancelled", "pending", "done"]:
    for chunk in graph.stream(inbound, config, stream_mode="updates"):
        if _cancel_requested(thread_id):
            _mark_force_stopped(graph, config, thread_id)
            emit({"type": "run_stopped", "reason": "force_stop", "status": "blocked"})
            return "cancelled"
        result = chunk if isinstance(chunk, dict) else {"value": chunk}
        interrupt = _interrupt_payload(result)
        if interrupt:
            emit(
                {
                    "type": "waiting_approval",
                    "gate": interrupt.get("gate"),
                    "prompt": interrupt.get("prompt"),
                    "payload": interrupt,
                }
            )
            return "interrupt"
        _emit_chunk_updates(thread_id, result)
    final = graph.get_state(config)
    interrupt = _interrupt_from_state(final)
    if interrupt:
        emit(
            {
                "type": "waiting_approval",
                "gate": interrupt.get("gate"),
                "prompt": interrupt.get("prompt"),
                "payload": interrupt,
            }
        )
        return "interrupt"
    if list(final.next or []):
        return "pending"
    return "done"


def _cancel_requested(thread_id: str) -> bool:
    return hub.stop_requested(thread_id)


def _clear_cancel(thread_id: str) -> None:
    hub.clear_stop_request(thread_id)


def _mark_force_stopped(graph, config: dict, thread_id: str) -> None:
    from memory import update_task_board

    try:
        state = graph.get_state(config)
        values = dict(state.values or {})
        task_title = (values.get("task") or "").strip() or thread_id
        activity = list(values.get("activity") or [])
        activity.append(
            {
                "kind": "gate",
                "from": "human",
                "text": "Supervisor force-stopped the office run.",
            }
        )
        graph.update_state(
            config,
            {
                "status": "blocked",
                "current_agent": "human",
                "activity": activity,
            },
        )
        update_task_board(thread_id, task_title, "blocked", "human")
    except Exception:  # noqa: BLE001
        pass


def _task_title_for_thread(thread_id: str, snap: dict[str, Any] | None = None) -> str:
    values = (snap or {}).get("values") or {}
    title = (values.get("task") or "").strip()
    if title:
        return title
    for row in list_tasks():
        if row.get("thread_id") == thread_id:
            return (row.get("task") or "").strip()
    return ""


def _carry_forward_state(values: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "plan",
        "design_spec",
        "scope_agreement",
        "architecture_brief",
        "implementation_summary",
        "files_written",
        "test_results",
        "ac_verification",
        "brief_answers",
        "brief_assumptions",
        "brief_message",
        "plan_approved",
        "scope_locked",
        "brief_confirmed",
    )
    return {k: values[k] for k in keys if values.get(k) is not None}


def continue_thread(thread_id: str, note: str = "") -> None:
    """Resume a stuck thread: pending checkpoint step, or PM-led continue for blocked/revising."""
    if is_busy(thread_id):
        raise RuntimeError("This thread is still running. Wait a moment and try again.")
    snap = snapshot(thread_id)
    if snap.get("interrupt"):
        raise RuntimeError("This thread is waiting at a gate — open it and use Approve or Send back.")
    task_title = _task_title_for_thread(thread_id, snap)
    if not task_title:
        raise RuntimeError("No task found for this thread on the board.")

    if snap.get("next"):
        pending = list(snap.get("next") or [])
        if pending == ["review"]:
            raise RuntimeError(
                "Release review is pending — refresh the page and use Sign release or Send back to PM."
            )
        update_task_board(thread_id, task_title, (snap.get("values") or {}).get("status") or "planning", "pm")
        _start(thread_id, None, task=task_title)
        return

    values = dict(snap.get("values") or {})
    prior_status = (values.get("status") or "").strip()
    board_row = next((r for r in list_tasks() if r.get("thread_id") == thread_id), {})
    if not prior_status:
        prior_status = (board_row.get("status") or "").strip()

    supervisor_note = (note or "").strip() or "Continue from the saved workspace and finish this slice."
    feedback = f"[Supervisor continue]\n{supervisor_note}"
    if values.get("feedback"):
        feedback = f"{feedback}\n\n{str(values['feedback'])[:1200]}"

    payload: dict[str, Any] = {
        "continue_run": True,
        "task": values.get("task") or task_title,
        "thread_id": thread_id,
        "feedback": feedback,
        "status": "revising",
        "history": list(values.get("history") or []),
        "activity": list(values.get("activity") or []),
        "dialogue": list(values.get("dialogue") or []),
        "retry_count": int(values.get("retry_count") or 0),
        "release_rejection_count": int(values.get("release_rejection_count") or 0),
        "scope_escalation_count": int(values.get("scope_escalation_count") or 0),
        "scope_locked": bool(values.get("scope_locked")),
        **(_carry_forward_state(values)),
    }
    if payload.get("plan") or prior_status in ("blocked", "revising") or not values:
        payload["release_triage"] = True
    if prior_status == "blocked":
        payload["release_rejection_count"] = max(0, payload["release_rejection_count"] - 1)
        payload["status"] = "revising"

    update_task_board(thread_id, payload["task"], "revising", "pm")
    _start(thread_id, payload, task=payload["task"])


def _execute(thread_id: str, payload: dict | Command | None) -> None:
    token_thread = thread_id_var.set(thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        with _run_lock:
            with make_checkpointer() as checkpointer:
                graph = compile_graph(checkpointer)
                inbound: dict | Command | None = payload
                release_chain: dict[str, Any] | None = None
                if isinstance(inbound, dict) and _RELEASE_CHAIN_KEY in inbound:
                    release_chain = inbound[_RELEASE_CHAIN_KEY]
                    inbound = None
                for _ in range(_MAX_GRAPH_DRAIN_STEPS):
                    outcome = _stream_until_pause(thread_id, graph, config, inbound)
                    if outcome == "interrupt":
                        if release_chain is not None:
                            inbound = Command(resume=release_chain)
                            release_chain = None
                            continue
                        return
                    if outcome == "cancelled":
                        return
                    final = graph.get_state(config)
                    pending = list(final.next or [])
                    if not pending:
                        values = final.values or {}
                        if _cancel_requested(thread_id):
                            _mark_force_stopped(graph, config, thread_id)
                            emit({"type": "run_stopped", "reason": "force_stop", "status": "blocked"})
                            return
                        emit({"type": "run_finished", "status": values.get("status") or "done"})
                        return
                    inbound = None
                final = graph.get_state(config)
                values = final.values or {}
                pending = list(final.next or [])
                if pending:
                    emit({"type": "pending_handoff", "nodes": pending})
                emit(
                    {
                        "type": "run_finished",
                        "status": values.get("status") or "stalled",
                        "pending_nodes": pending,
                        "message": (
                            f"Paused before {', '.join(pending)} — resuming automatically…"
                            if pending
                            else "Workflow finished."
                        ),
                    }
                )
    except Exception as exc:  # noqa: BLE001
        if _cancel_requested(thread_id):
            emit({"type": "run_stopped", "reason": "force_stop", "status": "blocked"})
        else:
            emit({"type": "error", "message": str(exc)})
    finally:
        thread_id_var.reset(token_thread)
        _clear_cancel(thread_id)
        with _active_lock:
            _active.discard(thread_id)


def _public(value: Any) -> Any:
    if isinstance(value, dict):
        skip = {"content"}
        return {k: v for k, v in value.items() if k not in skip and not (isinstance(v, str) and len(v) > 4000)}
    return value


def _start(thread_id: str, payload: dict | Command, task: str | None = None) -> None:
    _clear_cancel(thread_id)
    with _active_lock:
        if thread_id in _active:
            raise RuntimeError(f"Thread {thread_id} is already running")
        _active.add(thread_id)
    emit({"type": "run_started", "thread_id": thread_id, "task": task})
    threading.Thread(target=_execute, args=(thread_id, payload), daemon=True).start()


def start_task(task: str, thread_id: str | None = None) -> str:
    thread_id = thread_id or uuid.uuid4().hex[:12]
    update_task_board(thread_id, task.strip(), "planning", "pm")
    _start(
        thread_id,
        {
            "task": task,
            "thread_id": thread_id,
            "retry_count": 0,
            "release_rejection_count": 0,
            "scope_escalation_count": 0,
            "history": [],
            "activity": [],
            "dialogue": [],
            "scope_locked": False,
            "status": "planning",
        },
        task=task,
    )
    return thread_id


def open_release_gate_if_needed(thread_id: str) -> bool:
    """Drain into the release interrupt when review is next but the gate payload is not visible yet."""
    if is_busy(thread_id):
        return False
    current = snapshot(thread_id)
    if not current["exists"] or current.get("interrupt"):
        return False
    values = current.get("values") or {}
    pending = list(current.get("next") or [])
    if values.get("status") != "awaiting_release" and "review" not in pending:
        return False
    task = (values.get("task") or "").strip() or thread_id
    _start(thread_id, None, task=task)
    return True


def resume_task(thread_id: str, approved: bool, feedback: str = "") -> None:
    if is_busy(thread_id):
        raise RuntimeError("This thread is still running. Wait a moment and try again.")
    current = snapshot(thread_id)
    if not current["exists"]:
        raise RuntimeError(f"No checkpoint found for thread {thread_id}")
    interrupt = current.get("interrupt")
    if not interrupt:
        values = current.get("values") or {}
        pending = list(current.get("next") or [])
        if values.get("status") == "awaiting_release" or "review" in pending:
            task = (values.get("task") or "").strip() or thread_id
            _start(
                thread_id,
                {
                    _RELEASE_CHAIN_KEY: {
                        "approved": approved,
                        "feedback": feedback,
                    }
                },
                task=task,
            )
            return
        raise RuntimeError("Nothing is waiting for approval on this thread.")
    gate = interrupt.get("gate") if isinstance(interrupt, dict) else None
    if gate == "release" and approved and not feedback:
        feedback = ""
    _start(
        thread_id,
        Command(resume={"approved": approved, "feedback": feedback}),
        task=(current.get("values") or {}).get("task"),
    )


def is_busy(thread_id: str) -> bool:
    with _active_lock:
        return thread_id in _active


def list_active_runs() -> list[str]:
    with _active_lock:
        return sorted(_active)


def force_stop(thread_id: str | None = None, *, all_runs: bool = False) -> dict[str, Any]:
    """Request cooperative stop. In-flight LLM calls may finish one chunk before the run halts."""
    with _active_lock:
        if all_runs or not thread_id:
            targets = list(_active)
        elif thread_id in _active:
            targets = [thread_id]
        else:
            targets = []
    for tid in targets:
        hub.request_stop(tid)
    return {"requested": targets, "active": list_active_runs()}
