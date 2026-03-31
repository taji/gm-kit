"""Step registry for agent step definitions."""

from typing import TypedDict

from .base import AgentStepDefinition, Criticality


class StepDefinitionDict(TypedDict):
    """Schema for one static step definition."""

    phase: int
    description: str
    criticality: Criticality
    instruction_template: str
    contract_schema: str
    rubric_id: str


# Step definitions for all 13 agent steps (9.1 excluded)
STEP_DEFINITIONS: dict[str, StepDefinitionDict] = {
    "3.2": {
        "phase": 3,
        "description": "Parse visual TOC page",
        "criticality": Criticality.MEDIUM,
        "instruction_template": "instructions/step_3_2.md",
        "contract_schema": "schemas/step_3_2.schema.json",
        "rubric_id": "rubric_3_2",
    },
    "4.5": {
        "phase": 4,
        "description": "Resolve split sentences at chunk boundaries",
        "criticality": Criticality.LOW,
        "instruction_template": "instructions/step_4_5.md",
        "contract_schema": "schemas/step_4_5.schema.json",
        "rubric_id": "rubric_4_5",
    },
    "6.4": {
        "phase": 6,
        "description": "Fix spelling errors (OCR artifacts: rn->m, l->1, O->0)",
        "criticality": Criticality.LOW,
        "instruction_template": "instructions/step_6_4.md",
        "contract_schema": "schemas/step_6_4.schema.json",
        "rubric_id": "rubric_6_4",
    },
    "7.7": {
        "phase": 7,
        "description": "Detect table structures",
        "criticality": Criticality.MEDIUM,
        "instruction_template": "instructions/step_7_7.py",
        "contract_schema": "schemas/step_7_7.schema.json",
        "rubric_id": "rubric_7_7",
    },
    "8.7": {
        "phase": 8,
        "description": "Convert detected tables to markdown format",
        "criticality": Criticality.MEDIUM,
        "instruction_template": "instructions/step_8_7.md",
        "contract_schema": "schemas/step_8_7.schema.json",
        "rubric_id": "rubric_8_7",
    },
    "9.2": {
        "phase": 9,
        "description": "Structural clarity assessment",
        "criticality": Criticality.HIGH,
        "instruction_template": "instructions/step_9_2.md",
        "contract_schema": "schemas/step_9_2.schema.json",
        "rubric_id": "rubric_9_2",
    },
    "9.3": {
        "phase": 9,
        "description": "Text flow / readability assessment",
        "criticality": Criticality.HIGH,
        "instruction_template": "instructions/step_9_3.md",
        "contract_schema": "schemas/step_9_3.schema.json",
        "rubric_id": "rubric_9_3",
    },
    "9.4": {
        "phase": 9,
        "description": "Table integrity check",
        "criticality": Criticality.HIGH,
        "instruction_template": "instructions/step_9_4.md",
        "contract_schema": "schemas/step_9_4.schema.json",
        "rubric_id": "rubric_9_4",
    },
    "9.5": {
        "phase": 9,
        "description": "Callout formatting check",
        "criticality": Criticality.HIGH,
        "instruction_template": "instructions/step_9_5.md",
        "contract_schema": "schemas/step_9_5.schema.json",
        "rubric_id": "rubric_9_5",
    },
    "9.7": {
        "phase": 9,
        "description": "Review TOC validation issues (gaps, duplicates)",
        "criticality": Criticality.MEDIUM,
        "instruction_template": "instructions/step_9_7.md",
        "contract_schema": "schemas/step_9_7.schema.json",
        "rubric_id": "rubric_9_7",
    },
    "9.8": {
        "phase": 9,
        "description": "Review two-column reading order issues",
        "criticality": Criticality.MEDIUM,
        "instruction_template": "instructions/step_9_8.md",
        "contract_schema": "schemas/step_9_8.schema.json",
        "rubric_id": "rubric_9_8",
    },
    "10.2": {
        "phase": 10,
        "description": "Include quality ratings (1-5 scale)",
        "criticality": Criticality.LOW,
        "instruction_template": "instructions/step_10_2.md",
        "contract_schema": "schemas/step_10_2.schema.json",
        "rubric_id": "rubric_10_2",
    },
    "10.3": {
        "phase": 10,
        "description": "Document up to 3 remaining issues with examples",
        "criticality": Criticality.LOW,
        "instruction_template": "instructions/step_10_3.md",
        "contract_schema": "schemas/step_10_3.schema.json",
        "rubric_id": "rubric_10_3",
    },
}


class StepRegistry:
    """Registry for agent step definitions."""

    def __init__(self):
        """Initialize registry with step definitions."""
        self._steps: dict[str, AgentStepDefinition] = {}
        self._load_definitions()

    def _load_definitions(self) -> None:
        """Load step definitions into registry."""
        for step_id, defn in STEP_DEFINITIONS.items():
            self._steps[step_id] = AgentStepDefinition(
                step_id=step_id,
                phase=defn["phase"],
                description=defn["description"],
                criticality=defn["criticality"],
                instruction_template=defn["instruction_template"],
                contract_schema=defn["contract_schema"],
                rubric_id=defn.get("rubric_id"),
            )

    def get(self, step_id: str) -> AgentStepDefinition | None:
        """Get step definition by ID.

        Args:
            step_id: Step identifier (e.g., '3.2')

        Returns:
            Step definition or None if not found
        """
        return self._steps.get(step_id)

    def all_steps(self) -> list[AgentStepDefinition]:
        """Get all step definitions.

        Returns:
            List of all step definitions
        """
        return list(self._steps.values())

    def steps_by_phase(self, phase: int) -> list[AgentStepDefinition]:
        """Get all steps for a phase.

        Args:
            phase: Phase number

        Returns:
            List of steps in the phase
        """
        return [s for s in self._steps.values() if s.phase == phase]

    def get_criticality(self, step_id: str) -> Criticality | None:
        """Get criticality for a step.

        Args:
            step_id: Step identifier

        Returns:
            Criticality level or None if step not found
        """
        step = self._steps.get(step_id)
        return step.criticality if step else None


# Global registry instance
_registry: StepRegistry | None = None


def get_registry() -> StepRegistry:
    """Get the global step registry.

    Returns:
        StepRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = StepRegistry()
    return _registry
