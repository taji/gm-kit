import pytest

from gm_kit.validator import ValidationError, validate_agent, validate_os, validate_temp_path


def test_validate_temp_path__should_raise__when_empty():
    with pytest.raises(ValidationError, match="temp-path is required"):
        validate_temp_path("")


def test_validate_temp_path__should_create__when_missing(tmp_path):
    target = tmp_path / "new"
    result = validate_temp_path(str(target))

    assert result == target.resolve()
    assert result.exists()


def test_validate_temp_path__should_raise__when_mkdir_fails(tmp_path, monkeypatch):
    target = tmp_path / "nope"

    def _raise_mkdir(self, *args, **kwargs):
        raise OSError("nope")

    monkeypatch.setattr(type(target), "mkdir", _raise_mkdir)

    with pytest.raises(ValidationError, match="Unable to create temp path"):
        validate_temp_path(str(target))


def test_validate_temp_path__should_raise__when_not_writable(tmp_path, monkeypatch):
    target = tmp_path / "dir"
    target.mkdir()

    monkeypatch.setattr("gm_kit.validator.os.access", lambda _path, _mode: False)

    with pytest.raises(ValidationError, match="temp-path is not writable"):
        validate_temp_path(str(target))


def test_validate_os__should_normalize__when_case_varies():
    assert validate_os("WINDOWS") == "windows"
    assert validate_os("MacOS/Linux") == "macos/linux"


def test_validate_os__should_raise__when_missing():
    with pytest.raises(ValidationError, match="os is required"):
        validate_os(None)


def test_validate_os__should_raise__when_invalid_value():
    with pytest.raises(ValidationError, match="os must be"):
        validate_os("mac")


def test_validate_agent__should_return_config__when_supported():
    config = validate_agent("claude")
    assert config.name == "claude"


def test_validate_agent__should_raise__when_missing():
    with pytest.raises(ValidationError, match="agent is required"):
        validate_agent(None)


def test_validate_agent__should_raise__when_unsupported():
    with pytest.raises(ValidationError, match="Unsupported agent:"):
        validate_agent("unknown")
