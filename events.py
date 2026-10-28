from __future__ import annotations

import threading
from contextvars import ContextVar
from queue import Queue
from typing import Any

thread_id_var: ContextVar[str] = ContextVar("thread_id", default="")
agent_var: ContextVar[str] = ContextVar("agent", default="")


class EventHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: dict[str, list[Queue]] = {}
        self.live: dict[str, dict[str, Any]] = {}

    def subscribe(self, thread_id: str = "*") -> Queue:
        queue: Queue = Queue()
        with self._lock:
            self._subs.setdefault(thread_id, []).append(queue)
        return queue

    def unsubscribe(self, queue: Queue, thread_id: str = "*") -> None:
        with self._lock:
            if thread_id in self._subs:
                self._subs[thread_id] = [item for item in self._subs[thread_id] if item is not queue]

    def snapshot(self, thread_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self.live.get(thread_id) or {})

    def publish(self, thread_id: str, event: dict[str, Any]) -> None:
        payload = {"thread_id": thread_id, **event}
        with self._lock:
            current = self.live.setdefault(
                thread_id,
                {
                    "busy": False,
                    "working_agent": None,
                    "live_output": "",
                    "status": "idle",
                },
            )
            kind = payload.get("type")
            if kind == "run_started":
                current.update(
                    {
                        "busy": True,
                        "working_agent": None,
                        "live_output": "",
                        "status": "running",
                        "task": payload.get("task"),
                        "error": None,
                    }
                )
            elif kind == "agent_started":
                current.update(
                    {
                        "busy": True,
                        "working_agent": payload.get("agent"),
                        "live_output": "",
                        "status": "working",
                    }
                )
            elif kind == "model_selected":
                agent = payload.get("agent")
                model = payload.get("model")
                if agent and model:
                    in_use = current.setdefault("models_in_use", {})
                    in_use[agent] = model
                    current["active_model"] = model
                    current["active_model_agent"] = agent
            elif kind == "token":
                current["live_output"] = (current.get("live_output") or "") + str(payload.get("text") or "")
            elif kind == "agent_finished":
                agent = payload.get("agent")
                if agent:
                    last = current.setdefault("models_last_used", {})
                    in_use = current.get("models_in_use") or {}
                    if in_use.get(agent):
                        last[agent] = in_use[agent]
                if current.get("working_agent") == agent:
                    current["working_agent"] = None
                    current["active_model"] = None
                    current["active_model_agent"] = None
                    current["status"] = "running"
            elif kind == "waiting_approval":
                current.update({"busy": False, "working_agent": None, "status": "awaiting_human"})
            elif kind == "run_finished":
                current.update({"busy": False, "working_agent": None, "status": payload.get("status") or "done"})
            elif kind == "run_stopped":
                current.update(
                    {
                        "busy": False,
                        "working_agent": None,
                        "status": payload.get("status") or "blocked",
                        "error": None,
                    }
                )
            elif kind == "error":
                current.update(
                    {
                        "busy": False,
                        "working_agent": None,
                        "status": "error",
                        "error": payload.get("message"),
                    }
                )
            targets = list(self._subs.get(thread_id, [])) + list(self._subs.get("*", []))
        for queue in targets:
            queue.put(payload)


hub = EventHub()


def emit(event: dict[str, Any]) -> None:
    thread_id = event.get("thread_id") or thread_id_var.get()
    if not thread_id:
        return
    if "agent" not in event and agent_var.get():
        event = {**event, "agent": agent_var.get()}
    hub.publish(thread_id, event)
