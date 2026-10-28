from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel

from config import LLM_TEMPERATURE, MODELS_CONFIG_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL

AGENT_IDS = ("pm", "architect", "designer", "developer", "qa")


class ModelProfile(BaseModel):
    provider: Literal["ollama", "openai"] = "ollama"
    model: str = OLLAMA_MODEL
    base_url: str | None = None
    api_key_env: str | None = None
    temperature: float = LLM_TEMPERATURE

    def public_view(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "temperature": self.temperature,
            "api_key_set": bool(self.api_key_env and os.environ.get(self.api_key_env)),
        }


def _merge_profile(raw: dict[str, Any] | None, default: ModelProfile) -> ModelProfile:
    if not raw:
        return default
    data = default.model_dump()
    data.update({k: v for k, v in raw.items() if v is not None})
    return ModelProfile.model_validate(data)


@lru_cache
def load_models_config() -> dict[str, Any]:
    path = Path(MODELS_CONFIG_PATH)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML mapping")
    return data


def default_profile() -> ModelProfile:
    data = load_models_config()
    default_raw = data.get("default") or {}
    merged = {
        "provider": default_raw.get("provider", "ollama"),
        "model": default_raw.get("model", OLLAMA_MODEL),
        "base_url": default_raw.get("base_url") or OLLAMA_BASE_URL,
        "api_key_env": default_raw.get("api_key_env"),
        "temperature": default_raw.get("temperature", LLM_TEMPERATURE),
    }
    return ModelProfile.model_validate(merged)


def profile_for_agent(agent: str) -> ModelProfile:
    if agent not in AGENT_IDS:
        raise ValueError(f"Unknown agent: {agent}")
    data = load_models_config()
    agents = data.get("agents") or {}
    agent_raw = agents.get(agent)
    base = default_profile()
    if agent_raw is None:
        return base
    return _merge_profile(agent_raw if isinstance(agent_raw, dict) else {}, base)


def list_agent_models() -> dict[str, dict[str, Any]]:
    return {agent: profile_for_agent(agent).public_view() for agent in AGENT_IDS}


def reload_models_config() -> None:
    load_models_config.cache_clear()
