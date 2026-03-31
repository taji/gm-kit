from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from gm_kit.agent_registry import INIT_DISPLAY_AGENTS, canonicalize_agent


@dataclass(frozen=True)
class AgentConfig:
    name: str
    prompt_location: Path
    file_extension: str

    @property
    def format_type(self) -> str:
        return "toml" if self.file_extension == ".toml" else "md"


def _config(name: str, path: str, ext: str) -> AgentConfig:
    return AgentConfig(name=name, prompt_location=Path(path), file_extension=ext)


SUPPORTED_AGENTS: dict[str, AgentConfig] = {
    "claude": _config("claude", ".claude/commands", ".md"),
    "codex": _config("codex", ".codex/prompts", ".md"),
    "opencode": _config("opencode", ".opencode/command", ".md"),
    "gemini": _config("gemini", ".gemini/commands", ".toml"),
    "qwen": _config("qwen", ".qwen/commands", ".toml"),
}


def list_supported_agents() -> Iterable[str]:
    return INIT_DISPLAY_AGENTS


def get_agent_config(agent: str) -> AgentConfig:
    canonical = canonicalize_agent(agent, context="init")
    try:
        return SUPPORTED_AGENTS[canonical]
    except KeyError as exc:
        raise ValueError(f"Unsupported agent: {agent}") from exc


def is_supported(agent: str) -> bool:
    try:
        canonicalize_agent(agent, context="init")
        return True
    except ValueError:
        return False
