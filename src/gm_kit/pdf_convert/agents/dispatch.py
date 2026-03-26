"""Agent dispatch for CLI invocation.

Maps GM_AGENT environment variable to CLI invocations for different agents.
Supported: claude, codex, opencode, gemini, qwen
"""

import os
import subprocess
from typing import TypedDict, cast

from gm_kit.agent_registry import CANONICAL_AGENTS, canonicalize_agent


class AgentConfigDict(TypedDict, total=False):
    """Dispatch configuration for one agent CLI."""

    cli: str
    args: list[str]
    supports_stdin: bool
    uses_stdin_input: bool
    suppress_output: bool


# Agent CLI invocation templates
AGENT_DISPATCH_TABLE: dict[str, AgentConfigDict] = {
    "claude": {
        "cli": "claude",
        "args": ["--print", "--dangerously-skip-permissions"],
        "supports_stdin": True,
    },
    "codex": {
        "cli": "codex",
        "args": ["exec", "--full-auto", "-s", "workspace-write"],
        "supports_stdin": True,
        "uses_stdin_input": True,
        "suppress_output": True,
    },
    "opencode": {
        "cli": "opencode",
        "args": ["run"],
        "supports_stdin": False,
        "suppress_output": True,
    },
    "gemini": {
        "cli": "gemini",
        "args": [],  # Not CI-tested, minimal config
        "supports_stdin": False,
    },
    "qwen": {
        "cli": "qwen",
        "args": [],  # Not CI-tested, minimal config
        "supports_stdin": False,
    },
}

# CI-tested agents (confirmed by E2-09 audit)
CI_TESTED_AGENTS = ["claude", "codex", "opencode"]

DEFAULT_AGENT = "codex"
DEFAULT_AGENT_TIMEOUT_SEC = 300


class AgentDispatchError(Exception):
    """Exception raised when agent dispatch fails."""

    pass


class UnsupportedAgentError(AgentDispatchError):
    """Exception raised for unsupported agent."""

    pass


def get_agent_config(agent_name: str | None = None) -> AgentConfigDict:
    """Get configuration for an agent.

    Args:
        agent_name: Agent name (default: GM_AGENT env var or 'codex')

    Returns:
        Agent configuration dict

    Raises:
        UnsupportedAgentError: If agent not in dispatch table
    """
    if agent_name is None:
        agent_name = os.environ.get("GM_AGENT", DEFAULT_AGENT)

    try:
        agent_name = canonicalize_agent(agent_name, context="runtime")
    except ValueError as exc:
        supported = ", ".join(AGENT_DISPATCH_TABLE.keys())
        raise UnsupportedAgentError(
            f"Agent '{agent_name}' not supported. "
            f"Supported: {supported}. CI-tested: {', '.join(CI_TESTED_AGENTS)}"
        ) from exc

    if agent_name not in AGENT_DISPATCH_TABLE:
        supported = ", ".join(AGENT_DISPATCH_TABLE.keys())
        raise UnsupportedAgentError(
            f"Agent '{agent_name}' not supported. "
            f"Supported: {supported}. CI-tested: {', '.join(CI_TESTED_AGENTS)}"
        )

    return AGENT_DISPATCH_TABLE[agent_name]


def build_agent_command(prompt: str, workspace: str, agent_name: str | None = None) -> list[str]:
    """Build CLI command to invoke agent with prompt.

    Args:
        prompt: The prompt/instructions for the agent
        workspace: Workspace directory (for context)
        agent_name: Agent to use (default from env)

    Returns:
        Command as list of strings for subprocess
    """
    config = get_agent_config(agent_name)

    args = cast(list[str], config["args"])
    cmd: list[str] = [str(config["cli"]), *args]

    # Add prompt transport mode
    if config.get("uses_stdin_input", False):
        # Codex supports "-" to read prompt from stdin.
        cmd.append("-")
    else:
        cmd.append(prompt)

    return cmd


def invoke_agent(
    prompt: str, workspace: str, agent_name: str | None = None, capture_output: bool = False
) -> subprocess.CompletedProcess:
    """Invoke agent CLI with prompt.

    Args:
        prompt: Instructions for the agent
        workspace: Workspace directory
        agent_name: Agent to use
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess with return code

    Raises:
        AgentDispatchError: If invocation fails
        FileNotFoundError: If agent CLI not found
    """
    config = get_agent_config(agent_name)
    agent_name = agent_name or os.environ.get("GM_AGENT", DEFAULT_AGENT)

    # Build command
    cmd = build_agent_command(prompt, workspace, agent_name)

    suppress_output = config.get("suppress_output", False)
    use_stdin_input = config.get("uses_stdin_input", False)
    timeout_raw = os.environ.get("GM_AGENT_TIMEOUT_SEC", str(DEFAULT_AGENT_TIMEOUT_SEC))
    try:
        timeout_seconds = max(1, int(timeout_raw))
    except ValueError:
        timeout_seconds = DEFAULT_AGENT_TIMEOUT_SEC

    try:
        # Always execute with argv list (never shell command strings) to keep
        # multi-line prompts intact and avoid shell parsing issues.
        if suppress_output and not capture_output:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                text=True,
                timeout=timeout_seconds,
                input=prompt if use_stdin_input else None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=capture_output,
                text=True,
                timeout=timeout_seconds,
                input=prompt if use_stdin_input else None,
            )

        return result

    except FileNotFoundError as e:
        raise AgentDispatchError(
            f"Agent CLI '{config['cli']}' not found. Please install {agent_name} CLI."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise AgentDispatchError(
            f"Agent invocation timed out after {timeout_seconds} seconds"
        ) from e
    except Exception as e:
        raise AgentDispatchError(f"Failed to invoke agent: {e}") from e


def get_supported_agents() -> list[str]:
    """Get list of supported agents.

    Returns:
        List of supported agent names
    """
    return list(CANONICAL_AGENTS)


def get_ci_tested_agents() -> list[str]:
    """Get list of CI-tested agents (confirmed by E2-09).

    Returns:
        List of CI-tested agent names
    """
    return CI_TESTED_AGENTS.copy()


def is_agent_available(agent_name: str) -> bool:
    """Check if agent CLI is available on system.

    Args:
        agent_name: Agent to check

    Returns:
        True if agent CLI is in PATH
    """
    try:
        config = get_agent_config(agent_name)
        cli = config["cli"]

        # Check if in PATH
        result = subprocess.run(
            ["which", cli],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0

    except (UnsupportedAgentError, Exception):
        return False


def get_current_agent() -> str:
    """Get currently configured agent.

    Returns:
        Agent name from GM_AGENT or default
    """
    agent_name = os.environ.get("GM_AGENT", DEFAULT_AGENT)
    try:
        return canonicalize_agent(agent_name, context="runtime")
    except ValueError:
        return agent_name
