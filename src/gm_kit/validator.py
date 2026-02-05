from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from gm_kit.agent_config import AgentConfig, get_agent_config, is_supported

OSType = Literal["macos/linux", "windows"]


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_temp_path(temp_path: str) -> Path:
    if not temp_path:
        raise ValidationError("temp-path is required.")
    path = Path(temp_path).expanduser().resolve()
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValidationError(f"Unable to create temp path: {path}") from exc
    if not os.access(path, os.W_OK):
        raise ValidationError(f"temp-path is not writable: {path}")
    return path


def validate_os(os_type: str | None) -> OSType:
    if os_type is None:
        raise ValidationError("os is required (macos/linux or windows).")
    normalized = os_type.lower()
    if normalized not in ("macos/linux", "windows"):
        raise ValidationError("os must be 'macos/linux' or 'windows'.")
    return "windows" if normalized == "windows" else "macos/linux"


def validate_agent(agent: str | None) -> AgentConfig:
    if agent is None:
        raise ValidationError("agent is required (claude, codex-cli, gemini, qwen).")
    if not is_supported(agent):
        raise ValidationError(f"Unsupported agent: {agent}")
    return get_agent_config(agent)
