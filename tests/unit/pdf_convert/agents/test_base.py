"""Tests for agent step base types."""

from gm_kit.pdf_convert.agents.base import (
    AgentStepDefinition,
    AgentStepInputPayload,
    AgentStepOutputEnvelope,
    Criticality,
    StepStatus,
)


class TestAgentStepDefinition:
    """Test AgentStepDefinition dataclass."""

    def test_create_basic_definition(self):
        """Should create definition with required fields."""
        step = AgentStepDefinition(
            step_id="3.2",
            phase=3,
            description="Parse visual TOC",
            criticality=Criticality.MEDIUM,
            instruction_template="instructions/step_3_2.md",
            contract_schema="schemas/step_3_2.schema.json",
        )
        assert step.step_id == "3.2"
        assert step.phase == 3
        assert step.criticality == Criticality.MEDIUM
        assert step.rubric_id is None

    def test_create_with_rubric(self):
        """Should create definition with optional rubric."""
        step = AgentStepDefinition(
            step_id="9.2",
            phase=9,
            description="Structural clarity",
            criticality=Criticality.HIGH,
            instruction_template="instructions/step_9_2.md",
            contract_schema="schemas/step_9_2.schema.json",
            rubric_id="rubric_9_2",
        )
        assert step.rubric_id == "rubric_9_2"


class TestAgentStepInputPayload:
    """Test AgentStepInputPayload dataclass."""

    def test_create_payload(self):
        """Should create input payload with artifacts."""
        payload = AgentStepInputPayload(
            step_id="3.2",
            input_artifacts={"toc_text": "/path/to/toc.txt"},
            optional_artifacts={},
            context={"page_count": 50},
            output_contract="schemas/step_3_2.schema.json",
        )
        assert payload.step_id == "3.2"
        assert "toc_text" in payload.input_artifacts


class TestAgentStepOutputEnvelope:
    """Test AgentStepOutputEnvelope dataclass."""

    def test_create_envelope(self):
        """Should create output envelope with all fields."""
        envelope = AgentStepOutputEnvelope(
            step_id="3.2",
            status="success",
            data={"entries": []},
            warnings=[],
            notes="Test output",
            rubric_scores={"completeness": 5},
        )
        assert envelope.step_id == "3.2"
        assert envelope.status == "success"
        assert envelope.rubric_scores["completeness"] == 5


class TestEnums:
    """Test enum definitions."""

    def test_criticality_levels(self):
        """Should have three criticality levels."""
        assert Criticality.HIGH.value == "high"
        assert Criticality.MEDIUM.value == "medium"
        assert Criticality.LOW.value == "low"

    def test_step_status_values(self):
        """Should have all step statuses."""
        assert StepStatus.PENDING.name == "PENDING"
        assert StepStatus.COMPLETED.name == "COMPLETED"
        assert StepStatus.SKIPPED.name == "SKIPPED"
