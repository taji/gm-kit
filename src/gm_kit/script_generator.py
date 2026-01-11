from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

OSType = Literal["macos/linux", "windows"]


class ScriptGenerator:
    def __init__(self, asset_root_path: Path) -> None:
        self.bash_script_path = asset_root_path / "scripts" / "bash" / "say-hello.sh"
        self.ps_script_path = asset_root_path / "scripts" / "powershell" / "say-hello.ps1"

    def generate(self, os_type: OSType, target_root_path: Path) -> Path:
        if os_type == "windows":
            return self._copy_ps(target_root_path)
        return self._copy_bash(target_root_path)

    def _copy_bash(self, target_root_path: Path) -> Path:
        dest = target_root_path / ".gmkit" / "scripts" / "bash" / "say-hello.sh"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(self.bash_script_path, dest)
        dest.chmod(dest.stat().st_mode | 0o111)
        return dest

    def _copy_ps(self, target_root_path: Path) -> Path:
        dest = target_root_path / ".gmkit" / "scripts" / "powershell" / "say-hello.ps1"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(self.ps_script_path, dest)
        return dest
