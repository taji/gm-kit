from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

from gm_kit.agent_config import AgentConfig

# TOML descriptions for each command template
COMMAND_DESCRIPTIONS = {
    "gmkit.hello-gmkit": "GM-Kit Hello World command for TTRPG game mastering",
    "gmkit.pdf-to-markdown": "Convert PDF documents to Markdown for TTRPG game sessions",
}


class TemplateManager:
    def __init__(self, asset_root: Path) -> None:
        self.commands_dir = asset_root / "templates" / "commands"
        self.hello_template_path = asset_root / "templates" / "hello-gmkit-template.md"

    def copy_hello_template(self, target_root_path: Path) -> Path:
        dest = target_root_path / ".gmkit" / "templates" / "hello-gmkit-template.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(self.hello_template_path, dest)
        return dest

    def generate_prompt(self, agent: AgentConfig, target_root_path: Path) -> Path:
        """Generate prompts for all command templates. Returns path to prompt directory."""
        dest_dir = target_root_path / agent.prompt_location
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Install all command templates from the commands directory
        for template_path in self.commands_dir.glob("*.md"):
            self._install_command_prompt(template_path, agent, dest_dir)

        return dest_dir

    def _install_command_prompt(
        self, template_path: Path, agent: AgentConfig, dest_dir: Path
    ) -> Path:
        """Install a single command prompt to the agent's prompt location."""
        content = template_path.read_text()
        base_name = template_path.stem  # e.g., "gmkit.hello-gmkit"

        if agent.format_type == "md":
            dest = dest_dir / f"{base_name}.md"
            if not dest.exists():
                dest.write_text(content)
        else:
            dest = dest_dir / f"{base_name}.toml"
            if not dest.exists():
                description = COMMAND_DESCRIPTIONS.get(
                    base_name, f"GM-Kit command: {base_name}"
                )
                toml_text = self._build_toml(content, description)
                dest.write_text(toml_text)
            self.validate_toml(dest)
        return dest

    def list_command_prompts(self) -> list[str]:
        """List all available command prompt names."""
        return [p.stem for p in self.commands_dir.glob("*.md")]

    @staticmethod
    def validate_toml(path: Path) -> None:
        with path.open("rb") as fh:
            tomllib.load(fh)

    @staticmethod
    def _build_toml(markdown_content: str, description: str) -> str:
        return (
            f'description = "{description}"\n\n'
            'prompt = """\n'
            f"{markdown_content}\n"
            '"""\n'
        )
