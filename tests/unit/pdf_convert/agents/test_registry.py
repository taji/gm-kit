"""Test registry and step definitions."""

from gm_kit.pdf_convert.agents.base import Criticality
from gm_kit.pdf_convert.agents.registry import (
    STEP_DEFINITIONS,
    StepRegistry,
    get_registry,
)


class TestStepRegistry:
    """Test StepRegistry functionality."""

    def test_registry_contains_all_steps(self):
        """Should have all 13 agent steps."""
        registry = StepRegistry()
        all_steps = registry.all_steps()

        assert len(all_steps) == 13

    def test_get_step_by_id(self):
        """Should retrieve step by ID."""
        registry = StepRegistry()
        step = registry.get("3.2")

        assert step is not None
        assert step.step_id == "3.2"
        assert step.phase == 3

    def test_get_missing_step_returns_none(self):
        """Should return None for unknown step."""
        registry = StepRegistry()
        step = registry.get("99.99")

        assert step is None

    def test_steps_by_phase(self):
        """Should filter steps by phase."""
        registry = StepRegistry()
        phase_9_steps = registry.steps_by_phase(9)

        assert len(phase_9_steps) == 6  # 9.2, 9.3, 9.4, 9.5, 9.7, 9.8

        for step in phase_9_steps:
            assert step.phase == 9

    def test_criticality_lookup(self):
        """Should return criticality for step."""
        registry = StepRegistry()
        criticality = registry.get_criticality("9.2")

        assert criticality == Criticality.HIGH

    def test_step_9_1_excluded(self):
        """Step 9.1 should not be in registry."""
        registry = StepRegistry()
        step = registry.get("9.1")

        assert step is None


class TestGlobalRegistry:
    """Test global registry singleton."""

    def test_get_registry_returns_same_instance(self):
        """Should return singleton instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_global_registry_has_all_steps(self):
        """Global registry should have all steps."""
        registry = get_registry()

        assert len(registry.all_steps()) == 13


class TestStepDefinitionsDict:
    """Test STEP_DEFINITIONS constant."""

    def test_has_criticality(self):
        """All steps should have criticality defined."""
        for _step_id, defn in STEP_DEFINITIONS.items():
            assert "criticality" in defn
            assert defn["criticality"] in [
                Criticality.HIGH,
                Criticality.MEDIUM,
                Criticality.LOW,
            ]

    def test_has_instruction_template(self):
        """All steps should have instruction template."""
        for _step_id, defn in STEP_DEFINITIONS.items():
            assert "instruction_template" in defn
            assert defn["instruction_template"].startswith("instructions/")

    def test_has_contract_schema(self):
        """All steps should have contract schema."""
        for _step_id, defn in STEP_DEFINITIONS.items():
            assert "contract_schema" in defn
            assert defn["contract_schema"].startswith("schemas/")
