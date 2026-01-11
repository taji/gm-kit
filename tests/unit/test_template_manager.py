from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]

from gm_kit.agent_config import get_agent_config
import gm_kit
from gm_kit.template_manager import TemplateManager


def test_copy_hello_template_preserves_source(tmp_path):
    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    template_mgr = TemplateManager(asset_root)

    copied = template_mgr.copy_hello_template(tmp_path)

    assert copied.exists()
    assert copied.read_text() == (asset_root / "templates" / "hello-gmkit-template.md").read_text()


def test_generate_prompt_for_markdown_and_toml_agents(tmp_path):
    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    template_mgr = TemplateManager(asset_root)

    claude = get_agent_config("claude")
    md_path = template_mgr.generate_prompt(claude, tmp_path)
    assert md_path.suffix == ".md"
    command_md = (asset_root / "templates" / "commands" / "gmkit.hello-gmkit.md").read_text()
    assert md_path.read_text() == command_md

    gemini = get_agent_config("gemini")
    toml_path = template_mgr.generate_prompt(gemini, tmp_path)
    assert toml_path.suffix == ".toml"

    parsed = tomllib.loads(toml_path.read_text())
    assert parsed["description"].startswith("GM-Kit Hello World command")
    assert parsed["prompt"].strip() == command_md.strip()
