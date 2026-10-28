import json
from types import SimpleNamespace

from pydantic import BaseModel

import llm
from events import EventHub, RunCancelled, hub, thread_id_var
from model_config import ModelProfile


class Reply(BaseModel):
    message: str


def test_extract_json_uses_first_complete_object():
    text = '{"message":"first"}\n{"message":"repeated"}'

    assert llm.extract_json(text) == {"message": "first"}


def test_extract_json_preserves_fenced_code_inside_json():
    response = {
        "message": "README example",
        "content": "```bash\nnode tests.js\n```",
    }

    assert llm.extract_json(json.dumps(response)) == response
    assert llm.extract_json(f"```json\n{json.dumps(response)}\n```") == response


def test_extract_json_accepts_fenced_json_response():
    assert llm.extract_json('```json\n{"message":"ready"}\n```') == {"message": "ready"}


def test_token_reset_clears_previous_attempt_output():
    event_hub = EventHub()
    event_hub.publish("thread", {"type": "run_started"})
    event_hub.publish("thread", {"type": "token", "text": "invalid response"})
    event_hub.publish("thread", {"type": "token_reset"})

    assert event_hub.snapshot("thread")["live_output"] == ""


def test_ollama_model_receives_response_schema(monkeypatch):
    expected_schema = Reply.model_json_schema()
    captured = {}
    sentinel = object()

    def fake_chat_ollama(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(
        llm,
        "profile_for_agent",
        lambda _agent: ModelProfile(model="gemma4:test", provider="ollama"),
    )
    monkeypatch.setattr(llm, "ChatOllama", fake_chat_ollama)

    assert llm.get_model("pm", response_schema=expected_schema) is sentinel
    assert captured["format"] == expected_schema


def test_invoke_json_passes_schema_and_validates_response(monkeypatch):
    expected_schema = Reply.model_json_schema()
    captured = {}

    class FakeModel:
        def stream(self, _messages):
            yield SimpleNamespace(content='{"message":"ready"}')

    def fake_get_model(agent, response_schema=None):
        captured["agent"] = agent
        captured["response_schema"] = response_schema
        return FakeModel()

    monkeypatch.setattr(llm, "get_model", fake_get_model)

    result = llm.invoke_json("pm", "system", "user", Reply)

    assert result == {"message": "ready"}
    assert captured["agent"] == "pm"
    assert captured["response_schema"] == expected_schema


def test_invoke_json_stops_stream_after_first_valid_object(monkeypatch):
    class FakeModel:
        def stream(self, _messages):
            yield SimpleNamespace(content='{"message":"ready"}')
            raise AssertionError("continued consuming duplicate model output")

    monkeypatch.setattr(llm, "get_model", lambda *_args, **_kwargs: FakeModel())

    assert llm.invoke_json("pm", "system", "user", Reply) == {"message": "ready"}


def test_invoke_json_cancels_when_stop_is_requested(monkeypatch):
    thread_id = "llm-stop-test"

    class FakeModel:
        def stream(self, _messages):
            hub.request_stop(thread_id)
            yield SimpleNamespace(content='{"message":"not consumed"}')
            raise AssertionError("consumed another chunk after cancellation")

    monkeypatch.setattr(llm, "get_model", lambda *_args, **_kwargs: FakeModel())
    token = thread_id_var.set(thread_id)
    try:
        try:
            llm.invoke_json("pm", "system", "user", Reply)
        except RunCancelled:
            pass
        else:
            raise AssertionError("Expected model generation to be cancelled")
    finally:
        hub.clear_stop_request(thread_id)
        thread_id_var.reset(token)
