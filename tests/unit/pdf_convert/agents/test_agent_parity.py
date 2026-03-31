"""Parity checks between init and pdf-convert agent registries."""

from gm_kit.agent_config import SUPPORTED_AGENTS, get_agent_config, list_supported_agents
from gm_kit.agent_registry import CANONICAL_AGENTS
from gm_kit.pdf_convert.agents.dispatch import get_supported_agents


def test_agent_registries__should_match_canonical_set__when_comparing_init_and_runtime():
    init_supported = {config.name for config in SUPPORTED_AGENTS.values()}
    runtime_supported = set(get_supported_agents())
    canonical = set(CANONICAL_AGENTS)

    assert init_supported == canonical
    assert runtime_supported == canonical


def test_init_alias__should_resolve_to_codex__when_using_legacy_codex_cli_label():
    assert "codex-cli" in list(list_supported_agents())
    assert get_agent_config("codex-cli").name == "codex"
