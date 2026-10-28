from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from config import OFFICE_CONFIG_PATH

DEFAULT_OFFICE_NAME = "Agent Office"


class OfficeSignConfig(BaseModel):
    show: bool = True
    hide_baked_label: bool = True
    position: Literal["top", "bottom"] = "top"
    top_percent: float = 3.2
    bottom_percent: float = 3.8
    width_percent: float = 48.0


class OfficeConfig(BaseModel):
    name: str = DEFAULT_OFFICE_NAME
    sign: OfficeSignConfig = Field(default_factory=OfficeSignConfig)

    def public_view(self) -> dict[str, Any]:
        return {
            "name": self.name.strip() or DEFAULT_OFFICE_NAME,
            "sign": self.sign.model_dump(),
        }


def _parse_office(raw: dict[str, Any] | None) -> OfficeConfig:
    if not raw:
        return OfficeConfig()
    sign_raw = raw.get("sign")
    sign = OfficeSignConfig()
    if isinstance(sign_raw, dict):
        sign = OfficeSignConfig.model_validate(sign_raw)
    name = str(raw.get("name") or DEFAULT_OFFICE_NAME).strip() or DEFAULT_OFFICE_NAME
    return OfficeConfig(name=name, sign=sign)


@lru_cache
def load_office_config() -> OfficeConfig:
    path = Path(OFFICE_CONFIG_PATH)
    if not path.exists():
        return OfficeConfig()
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML mapping")
    return _parse_office(data)


def reload_office_config() -> OfficeConfig:
    load_office_config.cache_clear()
    return load_office_config()


def office_public_view() -> dict[str, Any]:
    return load_office_config().public_view()
