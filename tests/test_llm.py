from types import SimpleNamespace

from pydantic import BaseModel

import llm
from model_config import ModelProfile


class Reply(BaseModel):
    message: str


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
