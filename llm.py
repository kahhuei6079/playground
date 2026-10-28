import json
import os
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from config import JSON_PARSE_ATTEMPTS, OLLAMA_NUM_PREDICT
from events import emit
from model_config import profile_for_agent

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def get_model(agent: str) -> BaseChatModel:
    profile = profile_for_agent(agent)
    temperature = profile.temperature
    if profile.provider == "ollama":
        kwargs: dict[str, Any] = {
            "model": profile.model,
            "base_url": profile.base_url or "http://localhost:11434",
            "temperature": temperature,
            "num_predict": OLLAMA_NUM_PREDICT,
        }
        try:
            return ChatOllama(**kwargs, reasoning=False)
        except TypeError:
            kwargs.pop("num_predict", None)
            return ChatOllama(**kwargs)

    if profile.provider == "openai":
        from langchain_openai import ChatOpenAI

        if not profile.api_key_env:
            raise RuntimeError(
                f"Agent '{agent}' uses provider openai but api_key_env is not set in models.yaml"
            )
        api_key = os.environ.get(profile.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Agent '{agent}' expects {profile.api_key_env} in the environment for {profile.model}"
            )
        return ChatOpenAI(
            model=profile.model,
            temperature=temperature,
            api_key=api_key,
            base_url=profile.base_url,
        )

    raise RuntimeError(f"Unsupported provider '{profile.provider}' for agent '{agent}'")


def model_label(agent: str) -> str:
    profile = profile_for_agent(agent)
    if profile.provider == "ollama":
        return f"ollama/{profile.model}"
    return f"{profile.provider}/{profile.model}"


def extract_json(text: str) -> Any:
    cleaned = _THINK.sub("", text).strip()
    fenced = _FENCE.findall(cleaned)
    candidate = fenced[-1].strip() if fenced else cleaned
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model did not return JSON:\n{text[:800]}")
    return json.loads(candidate[start : end + 1])


def _chunk_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content)


def invoke_json(agent: str, system: str, user: str, schema: type[BaseModel]) -> dict[str, Any]:
    model = get_model(agent)
    label = model_label(agent)
    emit({"type": "model_selected", "agent": agent, "model": label})
    prompt = (
        f"{user}\n\n"
        "Return ONLY a JSON object that matches this schema. "
        "No markdown, no commentary.\n"
        f"{json.dumps(schema.model_json_schema(), indent=2)}"
    )
    last_error: Exception | None = None
    attempts = max(2, JSON_PARSE_ATTEMPTS)
    for attempt in range(attempts):
        retry_hint = ""
        if attempt > 0:
            retry_hint = (
                "\n\nPrevious output was invalid or incomplete JSON. "
                "Reply with ONE complete JSON object only (must end with balanced braces). "
                "If files[] made the response too long, use fewer, smaller files with minimal content."
            )
            err = str(last_error or "")
            if "did not return JSON" in err or "Unterminated" in err or "Expecting" in err:
                retry_hint += (
                    " Your last reply was likely truncated — shorten file contents and escape quotes in strings."
                )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt + retry_hint},
        ]
        parts: list[str] = []
        emit({"type": "token", "text": ""})
        for chunk in model.stream(messages):
            text = _chunk_text(getattr(chunk, "content", ""))
            if text:
                parts.append(text)
                emit({"type": "token", "text": text})
        content = "".join(parts)
        try:
            data = extract_json(content)
            return schema.model_validate(data).model_dump()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"Could not parse model JSON from {label}: {last_error}")
