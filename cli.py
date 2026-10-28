from __future__ import annotations

import argparse
import json
import uuid
from pprint import pprint

from langgraph.types import Command

from config import MAX_QA_RETRIES, OLLAMA_MODEL, WORKSPACE_DIR
from graph import compile_graph, make_checkpointer


def _interrupt_payload(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return None
    first = interrupts[0]
    return getattr(first, "value", first)


def _print_interrupt(payload: dict, thread_id: str) -> None:
    gate = payload.get("gate")
    print(f"\nPaused for human approval ({gate}).")
    print(f"Thread: {thread_id}")
    print(payload.get("prompt", ""))
    details = {k: v for k, v in payload.items() if k not in {"gate", "prompt"}}
    pprint(details)
    if gate == "brief":
        print(f"\nReply with answers:\n  python main.py approve {thread_id} --feedback \"your answers\"")
        print(f"Or use assumptions:\n  python main.py approve {thread_id}")
        return
    action = "approve" if gate == "plan" else "release"
    print(f"\nApprove:\n  python main.py {action} {thread_id}")
    print(f"Reject:\n  python main.py reject {thread_id} --feedback \"what to change\"")


def cmd_run(args: argparse.Namespace) -> None:
    thread_id = args.thread or uuid.uuid4().hex[:12]
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Starting task on model {OLLAMA_MODEL}")
    print(f"Thread: {thread_id}")
    print(f"Max QA retries: {MAX_QA_RETRIES}")
    with make_checkpointer() as checkpointer:
        graph = compile_graph(checkpointer)
        result = graph.invoke(
            {
                "task": args.task,
                "thread_id": thread_id,
                "retry_count": 0,
                "scope_escalation_count": 0,
                "history": [],
                "activity": [],
                "status": "planning",
            },
            config,
        )
        payload = _interrupt_payload(result)
        if payload:
            _print_interrupt(payload, thread_id)
            return
        print("Workflow finished.")
        pprint({k: result.get(k) for k in ("status", "qa_passed", "release_approved", "files_written")})


def _resume(thread_id: str, approved: bool, feedback: str) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    with make_checkpointer() as checkpointer:
        graph = compile_graph(checkpointer)
        snapshot = graph.get_state(config)
        if not snapshot.values:
            raise SystemExit(f"No checkpoint found for thread {thread_id}")
        result = graph.invoke(
            Command(resume={"approved": approved, "feedback": feedback}),
            config,
        )
        payload = _interrupt_payload(result)
        if payload:
            _print_interrupt(payload, thread_id)
            return
        values = graph.get_state(config).values
        print(f"Status: {values.get('status')}")
        if values.get("status") == "released":
            from memory import deliverable_info

            info = deliverable_info(thread_id)
            print(f"Folder: {info.get('folder') or WORKSPACE_DIR / thread_id}")
            if info.get("preview_url"):
                print(f"Preview: http://127.0.0.1:8000{info['preview_url']}")


def cmd_approve(args: argparse.Namespace) -> None:
    _resume(args.thread, True, args.feedback or "")


def cmd_release(args: argparse.Namespace) -> None:
    _resume(args.thread, True, args.feedback or "")


def cmd_reject(args: argparse.Namespace) -> None:
    if not args.feedback:
        raise SystemExit("Rejection requires --feedback so the next agent can revise.")
    _resume(args.thread, False, args.feedback)


def cmd_status(args: argparse.Namespace) -> None:
    config = {"configurable": {"thread_id": args.thread}}
    with make_checkpointer() as checkpointer:
        graph = compile_graph(checkpointer)
        snapshot = graph.get_state(config)
        if not snapshot.values:
            raise SystemExit(f"No checkpoint found for thread {args.thread}")
        values = snapshot.values
        print(json.dumps(
            {
                "thread": args.thread,
                "next": list(snapshot.next),
                "status": values.get("status"),
                "current_agent": values.get("current_agent"),
                "retry_count": values.get("retry_count"),
                "qa_passed": values.get("qa_passed"),
                "files_written": values.get("files_written"),
                "history": values.get("history"),
            },
            indent=2,
        ))
        if args.full:
            print("\nPlan:")
            pprint(values.get("plan"))
            print("\nQA:")
            pprint(values.get("test_results"))


def cmd_stop(args: argparse.Namespace) -> None:
    from runtime import force_stop, list_active_runs

    if args.all:
        result = force_stop(all_runs=True)
    elif args.thread:
        result = force_stop(args.thread)
    else:
        active = list_active_runs()
        if not active:
            print("No active runs.")
            return
        result = force_stop(all_runs=True)
    requested = result.get("requested") or []
    if requested:
        print(f"Stop requested for: {', '.join(requested)}")
    else:
        print("No matching active runs (already idle).")


def cmd_ui(args: argparse.Namespace) -> None:
    import webbrowser

    from server import run_server

    url = f"http://127.0.0.1:{args.port}"
    print(f"Agent Office UI: {url}")
    if not args.no_browser:
        webbrowser.open(url)
    run_server(port=args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local multi-agent office (LangGraph + Ollama)")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Submit a new task")
    run.add_argument("task")
    run.add_argument("--thread", help="Optional thread id")
    run.set_defaults(func=cmd_run)

    approve = sub.add_parser("approve", help="Approve the current gate (plan or release)")
    approve.add_argument("thread")
    approve.add_argument("--feedback", default="")
    approve.set_defaults(func=cmd_approve)

    release = sub.add_parser("release", help="Approve the release gate")
    release.add_argument("thread")
    release.add_argument("--feedback", default="")
    release.set_defaults(func=cmd_release)

    reject = sub.add_parser("reject", help="Reject the current gate with feedback")
    reject.add_argument("thread")
    reject.add_argument("--feedback", required=True)
    reject.set_defaults(func=cmd_reject)

    status = sub.add_parser("status", help="Show thread state")
    status.add_argument("thread")
    status.add_argument("--full", action="store_true")
    status.set_defaults(func=cmd_status)

    stop = sub.add_parser("stop", help="Force stop active agent run(s)")
    stop.add_argument("--thread", help="Stop a specific thread id")
    stop.add_argument("--all", action="store_true", help="Stop every active run")
    stop.set_defaults(func=cmd_stop)

    ui = sub.add_parser("ui", help="Open the live Agent Office dashboard")
    ui.add_argument("--port", type=int, default=8000)
    ui.add_argument("--no-browser", action="store_true", help="Do not open a browser tab automatically")
    ui.set_defaults(func=cmd_ui)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
