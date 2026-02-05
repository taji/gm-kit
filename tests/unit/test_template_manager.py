from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]

from gm_kit.agent_config import get_agent_config
from gm_kit.template_manager import TemplateManager


def _make_asset_root(tmp_path: Path) -> Path:
    asset_root = tmp_path / "assets"
    commands_dir = asset_root / "templates" / "commands"
    commands_dir.mkdir(parents=True)
    (asset_root / "templates").mkdir(exist_ok=True)
    (asset_root / "templates" / "hello-gmkit-template.md").write_text("hello template")
    (commands_dir / "gmkit.hello-gmkit.md").write_text("hello command")
    (commands_dir / "gmkit.pdf-to-markdown.md").write_text("pdf command")
    return asset_root


def test_copy_hello_template_preserves_source(tmp_path):
    asset_root = _make_asset_root(tmp_path)
    template_mgr = TemplateManager(asset_root)

    copied = template_mgr.copy_hello_template(tmp_path)

    assert copied.exists()
    assert copied.read_text() == (asset_root / "templates" / "hello-gmkit-template.md").read_text()


def test_generate_prompt_for_markdown_and_toml_agents(tmp_path):
    asset_root = _make_asset_root(tmp_path)
    template_mgr = TemplateManager(asset_root)

    # Test Claude (markdown format)
    claude = get_agent_config("claude")
    prompt_dir = template_mgr.generate_prompt(claude, tmp_path)
    assert prompt_dir.is_dir()

    # Verify hello-gmkit.md was created
    md_path = prompt_dir / "gmkit.hello-gmkit.md"
    assert md_path.exists()
    command_md = (asset_root / "templates" / "commands" / "gmkit.hello-gmkit.md").read_text()
    assert md_path.read_text() == command_md

    # Verify pdf-to-markdown.md was created
    pdf_md_path = prompt_dir / "gmkit.pdf-to-markdown.md"
    assert pdf_md_path.exists()

    # Test Gemini (TOML format) in a separate directory
    gemini_workspace = tmp_path / "gemini_test"
    gemini_workspace.mkdir()
    gemini = get_agent_config("gemini")
    toml_dir = template_mgr.generate_prompt(gemini, gemini_workspace)
    assert toml_dir.is_dir()

    toml_path = toml_dir / "gmkit.hello-gmkit.toml"
    assert toml_path.exists()

    parsed = tomllib.loads(toml_path.read_text())
    assert parsed["description"].startswith("GM-Kit Hello World command")
    assert parsed["prompt"].strip() == command_md.strip()

    # Verify pdf-to-markdown.toml was created
    pdf_toml_path = toml_dir / "gmkit.pdf-to-markdown.toml"
    assert pdf_toml_path.exists()
