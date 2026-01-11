from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional  # for type checking/hinting.

from gm_kit.agent_config import AgentConfig
from gm_kit.script_generator import ScriptGenerator
from gm_kit.template_manager import TemplateManager
from gm_kit.validator import validate_agent, validate_os, validate_temp_path


def _copy_constitution(asset_root: Path, target_root: Path) -> Path:
    source = asset_root / "memory" / "constitution.md"
    dest = target_root / ".gmkit" / "memory" / "constitution.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copyfile(source, dest)
    return dest


def run_init(temp_path: str, agent: Optional[str] = None, os_type: Optional[str] = None) -> Path:
    workspace = validate_temp_path(temp_path)
    agent_config: AgentConfig = validate_agent(agent)
    os_validated = validate_os(os_type)

    package_root_path = Path(__file__).resolve().parent
    asset_root_path = package_root_path / "assets"
    template_mgr = TemplateManager(asset_root_path)
    script_gen = ScriptGenerator(asset_root_path)

    # Copy templates and memory
    template_mgr.copy_hello_template(workspace)
    _copy_constitution(asset_root_path, workspace)

    # Generate prompt for the selected agent
    template_mgr.generate_prompt(agent_config, workspace)

    # Generate script for the selected OS
    script_gen.generate(os_validated, workspace)

    return workspace
