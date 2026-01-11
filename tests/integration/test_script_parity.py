import shutil
import subprocess
from pathlib import Path

import pytest

import gm_kit
from gm_kit.script_generator import ScriptGenerator
from gm_kit.template_manager import TemplateManager


def _prepare_workspace(tmp_path: Path):
    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    template_mgr = TemplateManager(asset_root)
    script_gen = ScriptGenerator(asset_root)

    template_mgr.copy_hello_template(tmp_path)
    bash_script = script_gen.generate("macos/linux", tmp_path)
    ps_script = script_gen.generate("windows", tmp_path)
    templates_dir = tmp_path / ".gmkit" / "templates"
    return bash_script, ps_script, templates_dir


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for parity test")
def test_script_parity_between_bash_and_powershell(tmp_path: Path):
    bash_script, ps_script, templates_dir = _prepare_workspace(tmp_path)
    greeting = "Hello from GM-Kit!"
    sequence = "05"

    bash_output = tmp_path / "bash-output"
    ps_output = tmp_path / "ps-output"

    bash_res = subprocess.run(
        [
            str(bash_script),
            "--greeting",
            greeting,
            "--sequence",
            sequence,
            "--templates-dir",
            str(templates_dir),
            "--output-dir",
            str(bash_output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    ps_res = subprocess.run(
        [
            "pwsh",
            "-File",
            str(ps_script),
            "-Greeting",
            greeting,
            "-Sequence",
            sequence,
            "-TemplatesDir",
            str(templates_dir),
            "-OutputDir",
            str(ps_output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    bash_file = bash_output / "greetings" / f"greeting{sequence}.md"
    ps_file = ps_output / "greetings" / f"greeting{sequence}.md"

    assert bash_file.exists()
    assert ps_file.exists()
    assert bash_file.read_text() == ps_file.read_text()
    assert bash_res.stdout.strip() == ps_res.stdout.strip()
