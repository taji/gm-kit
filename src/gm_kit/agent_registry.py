from __future__ import annotations

from typing import Literal

CANONICAL_AGENTS: tuple[str, ...] = ("claude", "codex", "opencode", "gemini", "qwen")

# Keep legacy init naming (`codex-cli`) while mapping to canonical runtime name (`codex`).
INIT_AGENT_ALIASES: dict[str, str] = {
    "claude": "claude",
    "codex": "codex",
    "codex-cli": "codex",
    "opencode": "opencode",
    "gemini": "gemini",
    "qwen": "qwen",
}

RUNTIME_AGENT_ALIASES: dict[str, str] = {
    "claude": "claude",
    "codex": "codex",
    "codex-cli": "codex",
    "opencode": "opencode",
    "gemini": "gemini",
    "qwen": "qwen",
}

# Agent labels shown to users in `gmkit init`.
INIT_DISPLAY_AGENTS: tuple[str, ...] = ("claude", "codex-cli", "opencode", "gemini", "qwen")


def canonicalize_agent(agent: str, context: Literal["init", "runtime"] = "runtime") -> str:
    """Map agent aliases to canonical names.

    Args:
        agent: User-provided agent identifier.
        context: Alias table context (`init` or `runtime`).

    Returns:
        Canonical agent name (e.g., `codex`).

    Raises:
        ValueError: If agent is unknown for the given context.
    """
    normalized = agent.lower().strip()
    aliases = INIT_AGENT_ALIASES if context == "init" else RUNTIME_AGENT_ALIASES
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported agent: {agent}") from exc
