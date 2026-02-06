"""Unit tests for CLI prompting and routing."""

from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from gm_kit import cli
from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.validator import ValidationError


def test_cli_prompt_text_choice__should_return_valid_value__when_user_retries(monkeypatch):
    """Prompt loops until a valid choice is entered."""
    responses = iter(["bad", "claude"])
    monkeypatch.setattr("typer.prompt", lambda _prompt: next(responses))

    assert cli._prompt_text_choice("Select agent", ["claude", "gemini"]) == "claude"


def test_cli_prompt_menu_choice__should_raise_exit__when_dependencies_missing(monkeypatch):
    """Missing readchar/rich raises Exit with guidance."""
    original_import = __import__

    def _raise_on_import(name, *args, **kwargs):
        # Simulate missing optional dependencies.
        if name.startswith("readchar") or name.startswith("rich"):
            raise ModuleNotFoundError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _raise_on_import)

    # Act against the function; it should raise a typer.Exit with code 1 for missing dependencies.
    with pytest.raises(cli.typer.Exit) as excinfo:
        cli._prompt_menu_choice("Select agent", ["claude"])

    assert excinfo.value.exit_code == 1


def test_cli_prompt_menu_choice__should_return_selected_option__when_enter_pressed(monkeypatch):
    """Menu selection returns the highlighted option."""
    fake_readchar = cast(Any, ModuleType("readchar"))
    fake_readchar.key = SimpleNamespace(
        UP="UP",
        DOWN="DOWN",
        CTRL_P="CTRL_P",
        CTRL_N="CTRL_N",
        ENTER="ENTER",
        CTRL_C="CTRL_C",
        ESC="ESC",
    )
    fake_readchar.readkey = lambda: fake_readchar.key.ENTER

    class FakeConsole:
        def __init__(self, *args, **kwargs):
            pass

    class FakeTableGrid:
        def add_row(self, *_args, **_kwargs):
            return None

    class FakeTable:
        @staticmethod
        def grid(*_args, **_kwargs):
            return FakeTableGrid()

    class FakePanel:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeLive:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, *_args, **_kwargs):
            return None

    monkeypatch.setitem(cli.sys.modules, "readchar", fake_readchar)
    monkeypatch.setitem(cli.sys.modules, "rich", ModuleType("rich"))
    monkeypatch.setitem(cli.sys.modules, "rich.console", ModuleType("rich.console"))
    monkeypatch.setitem(cli.sys.modules, "rich.live", ModuleType("rich.live"))
    monkeypatch.setitem(cli.sys.modules, "rich.panel", ModuleType("rich.panel"))
    monkeypatch.setitem(cli.sys.modules, "rich.table", ModuleType("rich.table"))
    monkeypatch.setattr(cli.sys.modules["rich.console"], "Console", FakeConsole, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.live"], "Live", FakeLive, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.panel"], "Panel", FakePanel, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.table"], "Table", FakeTable, raising=False)

    assert cli._prompt_menu_choice("Select agent", ["claude", "gemini"]) == "claude"


def test_cli_prompt_menu_choice__should_exit__when_escape_pressed(monkeypatch):
    """Escape exits the menu prompt."""
    fake_readchar = cast(Any, ModuleType("readchar"))
    fake_readchar.key = SimpleNamespace(
        UP="UP",
        DOWN="DOWN",
        CTRL_P="CTRL_P",
        CTRL_N="CTRL_N",
        ENTER="ENTER",
        CTRL_C="CTRL_C",
        ESC="ESC",
    )
    fake_readchar.readkey = lambda: fake_readchar.key.ESC

    class FakeConsole:
        def __init__(self, *args, **kwargs):
            pass

    class FakeTableGrid:
        def add_row(self, *_args, **_kwargs):
            return None

    class FakeTable:
        @staticmethod
        def grid(*_args, **_kwargs):
            return FakeTableGrid()

    class FakePanel:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeLive:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, *_args, **_kwargs):
            return None

    monkeypatch.setitem(cli.sys.modules, "readchar", fake_readchar)
    monkeypatch.setitem(cli.sys.modules, "rich", ModuleType("rich"))
    monkeypatch.setitem(cli.sys.modules, "rich.console", ModuleType("rich.console"))
    monkeypatch.setitem(cli.sys.modules, "rich.live", ModuleType("rich.live"))
    monkeypatch.setitem(cli.sys.modules, "rich.panel", ModuleType("rich.panel"))
    monkeypatch.setitem(cli.sys.modules, "rich.table", ModuleType("rich.table"))
    monkeypatch.setattr(cli.sys.modules["rich.console"], "Console", FakeConsole, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.live"], "Live", FakeLive, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.panel"], "Panel", FakePanel, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.table"], "Table", FakeTable, raising=False)

    with pytest.raises(cli.typer.Exit) as excinfo:
        cli._prompt_menu_choice("Select agent", ["claude", "gemini"])

    assert excinfo.value.exit_code == 1


def test_cli_prompt_menu_choice__should_move_selection__when_navigation_keys_pressed(
    monkeypatch,
):
    """Arrow keys change selection before enter."""
    fake_readchar = cast(Any, ModuleType("readchar"))
    fake_readchar.key = SimpleNamespace(
        UP="UP",
        DOWN="DOWN",
        CTRL_P="CTRL_P",
        CTRL_N="CTRL_N",
        ENTER="ENTER",
        CTRL_C="CTRL_C",
        ESC="ESC",
    )
    keys = iter([fake_readchar.key.DOWN, fake_readchar.key.UP, fake_readchar.key.ENTER])
    fake_readchar.readkey = lambda: next(keys)

    class FakeConsole:
        def __init__(self, *args, **kwargs):
            pass

    class FakeTableGrid:
        def add_row(self, *_args, **_kwargs):
            return None

    class FakeTable:
        @staticmethod
        def grid(*_args, **_kwargs):
            return FakeTableGrid()

    class FakePanel:
        def __init__(self, *_args, **_kwargs):
            pass

    class FakeLive:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, *_args, **_kwargs):
            return None

    monkeypatch.setitem(cli.sys.modules, "readchar", fake_readchar)
    monkeypatch.setitem(cli.sys.modules, "rich", ModuleType("rich"))
    monkeypatch.setitem(cli.sys.modules, "rich.console", ModuleType("rich.console"))
    monkeypatch.setitem(cli.sys.modules, "rich.live", ModuleType("rich.live"))
    monkeypatch.setitem(cli.sys.modules, "rich.panel", ModuleType("rich.panel"))
    monkeypatch.setitem(cli.sys.modules, "rich.table", ModuleType("rich.table"))
    monkeypatch.setattr(cli.sys.modules["rich.console"], "Console", FakeConsole, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.live"], "Live", FakeLive, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.panel"], "Panel", FakePanel, raising=False)
    monkeypatch.setattr(cli.sys.modules["rich.table"], "Table", FakeTable, raising=False)

    assert cli._prompt_menu_choice("Select agent", ["claude", "gemini"]) == "claude"


def test_cli_init__should_use_text_prompts__when_not_tty(monkeypatch, tmp_path):
    """init uses text prompts when stdin/stdout are non-tty."""
    runner = CliRunner()
    calls = {"text_prompt": 0}
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(
        cli,
        "_prompt_text_choice",
        lambda *_args, **_kwargs: calls.__setitem__("text_prompt", calls["text_prompt"] + 1)
        or "claude",
    )
    monkeypatch.setattr(
        cli,
        "_prompt_menu_choice",
        lambda *_args, **_kwargs: pytest.fail("Menu prompt should not be used when not a TTY"),
    )
    monkeypatch.setattr(cli, "run_init", lambda *_args, **_kwargs: tmp_path)
    monkeypatch.setattr(
        cli,
        "get_agent_config",
        lambda _agent: SimpleNamespace(prompt_location="prompts", file_extension=".md"),
    )
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)

    result = runner.invoke(cli.app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert calls["text_prompt"] > 0
    assert "Initializing workspace..." in result.output


def test_cli_init__should_exit_with_error__when_validation_fails(monkeypatch, tmp_path):
    """init fails with ValidationError from run_init."""
    runner = CliRunner()
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(cli, "_prompt_text_choice", lambda *_args, **_kwargs: "claude")
    monkeypatch.setattr(
        cli,
        "run_init",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValidationError("bad config")),
    )
    monkeypatch.setattr(
        cli,
        "get_agent_config",
        lambda _agent: SimpleNamespace(prompt_location="prompts", file_extension=".md"),
    )

    result = runner.invoke(cli.app, ["init", str(tmp_path)])
    # Expect: "bad config"
    assert result.exit_code == 1
    assert "bad config" in result.output


def test_cli_init__should_use_menu_prompts__when_tty(monkeypatch, tmp_path):
    """init uses menu prompts when TTY and not forced to text."""
    expected_menu_calls = 2
    calls = {"menu": 0}
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)

    def _menu_choice(*_args, **_kwargs):
        calls["menu"] += 1
        return "claude" if calls["menu"] == 1 else "macos/linux"

    monkeypatch.setattr(cli, "_prompt_menu_choice", _menu_choice)
    monkeypatch.setattr(cli, "run_init", lambda *_a, **_k: tmp_path)
    monkeypatch.setattr(
        cli,
        "get_agent_config",
        lambda _agent: SimpleNamespace(prompt_location="prompts", file_extension=".md"),
    )
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)

    cli.init(str(tmp_path), agent=None, os=None, text_input=False)
    assert calls["menu"] == expected_menu_calls


def test_cli_main__should_call_app(monkeypatch):
    """main delegates to the Typer app."""
    called = {"app": False}
    monkeypatch.setattr(cli, "app", lambda: called.__setitem__("app", True))

    cli.main()
    assert called["app"] is True


def test_cli_module__should_run_main__when_executed_as_script(monkeypatch):
    """__main__ execution runs the CLI entrypoint."""
    import runpy

    monkeypatch.setattr(cli.sys, "argv", ["gm_kit.cli"])

    with pytest.raises(SystemExit):
        runpy.run_module("gm_kit.cli", run_name="__main__")


def test_cli_pdf_convert__should_exit_with_success__when_status_requested(monkeypatch):
    """--status returns orchestrator exit code."""
    runner = CliRunner()

    class StubOrchestrator:
        def show_status(self, _path):
            return ExitCode.SUCCESS

    monkeypatch.setattr(
        "gm_kit.pdf_convert.orchestrator.Orchestrator",
        StubOrchestrator,
    )

    result = runner.invoke(cli.app, ["pdf-convert", "--status", "output"])
    assert result.exit_code == ExitCode.SUCCESS


def test_cli_pdf_convert__should_return_exit_code__when_error_simulated_with_resume_flag(
    monkeypatch,
):
    """--resume returns orchestrator exit code."""
    runner = CliRunner()

    class StubOrchestrator:
        def resume_conversion(self, _path, auto_proceed=False):
            return ExitCode.STATE_ERROR

    monkeypatch.setattr(
        "gm_kit.pdf_convert.orchestrator.Orchestrator",
        StubOrchestrator,
    )

    result = runner.invoke(cli.app, ["pdf-convert", "--resume", "output"])
    assert result.exit_code == ExitCode.STATE_ERROR


def test_cli_pdf_convert__should_use_active_conversion__when_resume_without_path(
    monkeypatch,
    tmp_path,
):
    """--resume without a path uses active conversion state."""
    from gm_kit.pdf_convert.active_conversion import update_active_conversion

    runner = CliRunner()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    update_active_conversion(tmp_path, output_dir)

    class StubOrchestrator:
        def resume_conversion(self, path, auto_proceed=False):
            assert path == output_dir
            return ExitCode.SUCCESS

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "gm_kit.pdf_convert.orchestrator.Orchestrator",
        StubOrchestrator,
    )

    result = runner.invoke(cli.app, ["pdf-convert", "--resume"])
    assert result.exit_code == ExitCode.SUCCESS


def test_cli_pdf_convert__should_error__when_pdf_path_missing():
    """Missing pdf_path returns FILE_ERROR and usage."""
    runner = CliRunner()
    result = runner.invoke(cli.app, ["pdf-convert"])

    assert result.exit_code == ExitCode.FILE_ERROR
    assert "ERROR: PDF path is required for new conversion" in result.output
