from pathlib import Path

import pytest

from gm_kit.init import run_init
from gm_kit.validator import ValidationError


class _FakeTemplateManager:
    def __init__(self, _asset_root: Path) -> None:
        pass

    def copy_hello_template(self, target_root: Path) -> Path:
        dest = target_root / ".gmkit" / "templates" / "hello-gmkit-template.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_text("hello template")
        return dest

    def generate_prompt(self, agent, target_root: Path) -> Path:
        dest_dir = target_root / agent.prompt_location
        dest_dir.mkdir(parents=True, exist_ok=True)
        prompt = dest_dir / "gmkit.hello-gmkit.md"
        if not prompt.exists():
            prompt.write_text("hello prompt")
        return dest_dir


class _FakeScriptGenerator:
    def __init__(self, _asset_root: Path) -> None:
        pass

    def generate(self, os_type: str, target_root: Path) -> Path:
        if os_type == "windows":
            dest = target_root / ".gmkit" / "scripts" / "powershell" / "say-hello.ps1"
        else:
            dest = target_root / ".gmkit" / "scripts" / "bash" / "say-hello.sh"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_text("script")
        return dest


def _fake_copy_constitution(_asset_root: Path, target_root: Path) -> Path:
    dest = target_root / ".gmkit" / "memory" / "constitution.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_text("constitution")
    return dest


@pytest.fixture(autouse=True)
def _patch_asset_dependencies(monkeypatch):
    monkeypatch.setattr("gm_kit.init.TemplateManager", _FakeTemplateManager)
    monkeypatch.setattr("gm_kit.init.ScriptGenerator", _FakeScriptGenerator)
    monkeypatch.setattr("gm_kit.init._copy_constitution", _fake_copy_constitution)


def test_run_init_rejects_invalid_os(tmp_path):
    with pytest.raises(ValidationError):
        run_init(temp_path=str(tmp_path), agent="claude", os_type="unsupported")


def test_run_init_rejects_invalid_agent(tmp_path):
    with pytest.raises(ValidationError):
        run_init(temp_path=str(tmp_path), agent="invalid", os_type="macos/linux")


def test_run_init_creates_temp_path(tmp_path):
    workspace = tmp_path / "new"
    path = run_init(temp_path=str(workspace), agent="claude", os_type="macos/linux")
    assert path.exists()
    assert (workspace / ".gmkit").exists()


def test_run_init_is_idempotent_and_preserves_existing_files(tmp_path):
    # Run init twice to ensure idempotency
    workspace = tmp_path / "workspace"
    run_init(temp_path=str(workspace), agent="claude", os_type="macos/linux")

    hello_template = workspace / ".gmkit" / "templates" / "hello-gmkit-template.md"
    script_path = workspace / ".gmkit" / "scripts" / "bash" / "say-hello.sh"
    constitution = workspace / ".gmkit" / "memory" / "constitution.md"
    prompt = workspace / ".claude" / "commands" / "gmkit.hello-gmkit.md"

    # Modify the files to ensure they are preserved on re-initialization
    hello_template.write_text("custom template")
    script_path.write_text("#!/usr/bin/env bash\necho custom script\n")
    constitution.write_text("custom constitution")
    prompt.write_text("custom prompt")

    # Re-run init, should not overwrite existing files.
    run_init(temp_path=str(workspace), agent="claude", os_type="macos/linux")

    assert hello_template.read_text() == "custom template"
    assert script_path.read_text() == "#!/usr/bin/env bash\necho custom script\n"
    assert constitution.read_text() == "custom constitution"
    assert prompt.read_text() == "custom prompt"
