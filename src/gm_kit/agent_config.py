from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


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
    "codex-cli": _config("codex-cli", ".codex/prompts", ".md"),
    "gemini": _config("gemini", ".gemini/commands", ".toml"),
    "qwen": _config("qwen", ".qwen/commands", ".toml"),
}


def list_supported_agents() -> Iterable[str]:
    return SUPPORTED_AGENTS.keys()


def get_agent_config(agent: str) -> AgentConfig:
    try:
        return SUPPORTED_AGENTS[agent]
    except KeyError as exc:
        raise ValueError(f"Unsupported agent: {agent}") from exc


def is_supported(agent: str) -> bool:
    return agent in SUPPORTED_AGENTS
