from __future__ import annotations

import shutil
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore[import-not-found]

from gm_kit.agent_config import AgentConfig


class TemplateManager:
    def __init__(self, asset_root: Path) -> None:
        self.command_template_path = asset_root / "templates" / "commands" / "gmkit.hello-gmkit.md"
        self.hello_template_path = asset_root / "templates" / "hello-gmkit-template.md"

    def copy_hello_template(self, target_root_path: Path) -> Path:
        dest = target_root_path / ".gmkit" / "templates" / "hello-gmkit-template.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(self.hello_template_path, dest)
        return dest

    def generate_prompt(self, agent: AgentConfig, target_root_path: Path) -> Path:
        content = self.command_template_path.read_text()
        dest_dir = target_root_path / agent.prompt_location
        dest_dir.mkdir(parents=True, exist_ok=True)
        if agent.format_type == "md":
            dest = dest_dir / "gmkit.hello-gmkit.md"
            if not dest.exists():
                dest.write_text(content)
        else:
            dest = dest_dir / "gmkit.hello-gmkit.toml"
            if not dest.exists():
                toml_text = self._build_toml(content)
                dest.write_text(toml_text)
            self.validate_toml(dest)
        return dest

    @staticmethod
    def validate_toml(path: Path) -> None:
        with path.open("rb") as fh:
            tomllib.load(fh)

    @staticmethod
    def _build_toml(markdown_content: str) -> str:
        return (
            'description = "GM-Kit Hello World command for TTRPG game mastering"\n\n'
            'prompt = """\n'
            f"{markdown_content}\n"
            '"""\n'
        )
