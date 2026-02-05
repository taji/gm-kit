import os
from pathlib import Path

from gm_kit.script_generator import ScriptGenerator


def _make_asset_root(tmp_path: Path) -> Path:
    asset_root = tmp_path / "assets"
    (asset_root / "scripts" / "bash").mkdir(parents=True)
    (asset_root / "scripts" / "powershell").mkdir(parents=True)
    (asset_root / "scripts" / "bash" / "say-hello.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    (asset_root / "scripts" / "powershell" / "say-hello.ps1").write_text("Write-Host hi\n")
    return asset_root


def test_generate_scripts_copies_and_sets_permissions(tmp_path):
    asset_root = _make_asset_root(tmp_path)
    generator = ScriptGenerator(asset_root)

    bash_path = generator.generate("macos/linux", tmp_path)
    ps_path = generator.generate("windows", tmp_path)

    assert bash_path.exists()
    assert os.access(bash_path, os.X_OK)
    assert bash_path.parent.name == "bash"

    assert ps_path.exists()
    assert ps_path.suffix == ".ps1"
    assert ps_path.parent.name == "powershell"
