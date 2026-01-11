from pathlib import Path

import pytest

from gm_kit.agent_config import (
    SUPPORTED_AGENTS,
    get_agent_config,
    is_supported,
    list_supported_agents,
)


def test_supported_agents_listing_matches_registry():
    names = list(list_supported_agents())
    assert set(names) == set(SUPPORTED_AGENTS.keys())


def test_agent_configs_have_expected_locations_and_formats():
    claude = get_agent_config("claude")
    assert claude.prompt_location == Path(".claude/commands")
    assert claude.file_extension == ".md"
    assert claude.format_type == "md"

    gemini = get_agent_config("gemini")
    assert gemini.prompt_location == Path(".gemini/commands")
    assert gemini.file_extension == ".toml"
    assert gemini.format_type == "toml"


def test_is_supported_and_get_agent_config_enforces_registry():
    assert is_supported("qwen") is True
    assert is_supported("unknown") is False
    with pytest.raises(ValueError):
        get_agent_config("unknown")
