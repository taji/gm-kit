from pathlib import Path

from typer.testing import CliRunner

from gm_kit.cli import app

runner = CliRunner()


def test_cli_init_creates_workspace(tmp_path: Path):
    temp = tmp_path / "workspace"
    result = runner.invoke(
        app,
        [
            "init",
            str(temp),
            "--agent",
            "claude",
            "--os",
            "macos/linux",
            "--text-input",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (temp / ".gmkit" / "templates" / "hello-gmkit-template.md").exists()
    assert (temp / ".gmkit" / "scripts" / "bash" / "say-hello.sh").exists()
    assert (temp / ".gmkit" / "memory" / "constitution.md").exists()
    assert (temp / ".claude" / "commands" / "gmkit.hello-gmkit.md").exists()


def test_cli_init_rejects_invalid_agent(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "init",
            str(tmp_path / "workspace"),
            "--agent",
            "invalid",
            "--os",
            "macos/linux",
            "--text-input",
        ],
    )
    assert result.exit_code != 0
    assert "Unsupported agent" in result.output or "invalid" in result.output.lower()


def test_cli_init_prompts_for_missing_agent_and_os(tmp_path: Path):
    temp = tmp_path / "workspace"
    result = runner.invoke(
        app,
        ["init", str(temp), "--text-input"],
        input="claude\nmacos/linux\n",  # Provide agent and OS choices via prompts (delimited by newlines).
    )
    assert result.exit_code == 0, result.output
    assert (temp / ".gmkit" / "templates" / "hello-gmkit-template.md").exists()
