from pathlib import Path

import pytest

from gm_kit.init import run_init
from gm_kit.validator import ValidationError


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
