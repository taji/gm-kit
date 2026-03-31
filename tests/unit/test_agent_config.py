from pathlib import Path

import pytest

from gm_kit.agent_config import (
    get_agent_config,
    is_supported,
    list_supported_agents,
)
from gm_kit.agent_registry import INIT_DISPLAY_AGENTS


def test_supported_agents_listing_matches_registry():
    names = list(list_supported_agents())
    assert names == list(INIT_DISPLAY_AGENTS)


def test_agent_configs_have_expected_locations_and_formats():
    claude = get_agent_config("claude")
    assert claude.prompt_location == Path(".claude/commands")
    assert claude.file_extension == ".md"
    assert claude.format_type == "md"

    opencode = get_agent_config("opencode")
    assert opencode.prompt_location == Path(".opencode/command")
    assert opencode.file_extension == ".md"
    assert opencode.format_type == "md"

    gemini = get_agent_config("gemini")
    assert gemini.prompt_location == Path(".gemini/commands")
    assert gemini.file_extension == ".toml"
    assert gemini.format_type == "toml"


def test_is_supported_and_get_agent_config_enforces_registry():
    assert is_supported("qwen") is True
    assert is_supported("codex-cli") is True
    assert is_supported("unknown") is False
    assert get_agent_config("codex-cli").name == "codex"
    with pytest.raises(ValueError):
        get_agent_config("unknown")
