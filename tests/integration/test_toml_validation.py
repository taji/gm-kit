from pathlib import Path

import pytest

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]

import gm_kit
from gm_kit.agent_config import get_agent_config
from gm_kit.template_manager import TemplateManager


def test_validate_toml_accepts_generated_prompt(tmp_path: Path):
    asset_root = Path(gm_kit.__file__).resolve().parent / "assets"
    tmpl = TemplateManager(asset_root)
    gemini = get_agent_config("gemini")

    toml_dir = tmpl.generate_prompt(gemini, tmp_path)
    # Validate all generated TOML files
    for toml_path in toml_dir.glob("*.toml"):
        tmpl.validate_toml(toml_path)  # should not raise


def test_validate_toml_rejects_invalid_file(tmp_path: Path):
    bad = tmp_path / "bad.toml"
    bad.write_text("prompt = \"\"\"\nunterminated")

    with pytest.raises(tomllib.TOMLDecodeError):
        TemplateManager.validate_toml(bad)
