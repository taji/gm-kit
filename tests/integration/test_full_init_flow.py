from pathlib import Path

import gm_kit
from gm_kit.init import run_init


def _read(path: Path) -> str:
    return path.read_text()


def test_full_init_flow_claude(tmp_path):
    workspace = tmp_path / "workspace"
    run_init(temp_path=str(workspace), agent="claude", os_type="macos/linux")

    hello_template = workspace / ".gmkit" / "templates" / "hello-gmkit-template.md"
    script_path = workspace / ".gmkit" / "scripts" / "bash" / "say-hello.sh"
    constitution = workspace / ".gmkit" / "memory" / "constitution.md"
    prompt = workspace / ".claude" / "commands" / "gmkit.hello-gmkit.md"

    assert hello_template.exists()
    assert script_path.exists()
    assert constitution.exists()
    assert prompt.exists()

    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    assert _read(hello_template) == _read(asset_root / "templates" / "hello-gmkit-template.md")
    assert _read(prompt) == _read(asset_root / "templates" / "commands" / "gmkit.hello-gmkit.md")
