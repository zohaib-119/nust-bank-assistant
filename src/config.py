"""Configuration utilities for the Bank RAG Assistant.

Single source-of-truth for environment variables and runtime settings.

Keep this module dependency-light so it can be imported everywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _env_int(name: str, default: int) -> int:
    v = _env(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    # LLM
    ollama_model: str = _env("OLLAMA_MODEL", "llama3.2")  # type: ignore[arg-type]

    # Retrieval
    top_k: int = _env_int("TOP_K", 3)

    # Guardrails
    enable_guardrails: bool = (_env("ENABLE_GUARDRAILS", "1") not in ("0", "false", "False"))

    # UI
    ui_host: str = _env("UI_HOST", "127.0.0.1")  # type: ignore[arg-type]
    ui_port: int = _env_int("UI_PORT", 7860)


CONFIG = AppConfig()
