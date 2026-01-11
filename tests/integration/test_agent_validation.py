import pytest

from gm_kit.validator import ValidationError, validate_agent, validate_os


def test_validate_agent_accepts_supported_agents():
    config = validate_agent("claude")
    assert config.name == "claude"


def test_validate_agent_rejects_missing_or_unknown():
    with pytest.raises(ValidationError):
        validate_agent(None)
    with pytest.raises(ValidationError):
        validate_agent("unknown")


def test_validate_os_enforces_known_values():
    assert validate_os("macos/linux") == "macos/linux"
    assert validate_os("windows") == "windows"
    with pytest.raises(ValidationError):
        validate_os(None)
    with pytest.raises(ValidationError):
        validate_os("mac")
