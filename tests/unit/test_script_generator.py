import os
from pathlib import Path

import gm_kit
from gm_kit.script_generator import ScriptGenerator


def test_generate_scripts_copies_and_sets_permissions(tmp_path):
    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    generator = ScriptGenerator(asset_root)

    bash_path = generator.generate("macos/linux", tmp_path)
    ps_path = generator.generate("windows", tmp_path)

    assert bash_path.exists()
    assert os.access(bash_path, os.X_OK)
    assert bash_path.parent.name == "bash"

    assert ps_path.exists()
    assert ps_path.suffix == ".ps1"
    assert ps_path.parent.name == "powershell"
