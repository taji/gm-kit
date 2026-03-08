"""Tests for workspace I/O helpers."""

import json

import pytest

from gm_kit.pdf_convert.agents.agent_step import (
    read_agent_output,
    write_agent_inputs,
)
from gm_kit.pdf_convert.agents.errors import AgentStepError


class TestWriteAgentInputs:
    """Test write_agent_inputs function."""

    def test_creates_step_directory(self, tmp_path):
        """Should create step directory structure."""
        step_dir = write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"test": "data"},
        )

        assert step_dir.exists()
        assert step_dir.name == "step_3_2"
        assert (step_dir.parent.parent / "agent_steps").exists()

    def test_writes_input_json(self, tmp_path):
        """Should write step-input.json."""
        write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"toc_text": "sample"},
        )

        input_file = tmp_path / "agent_steps" / "step_3_2" / "step-input.json"
        assert input_file.exists()

        with open(input_file) as f:
            data = json.load(f)

        assert data["step_id"] == "3.2"
        assert data["toc_text"] == "sample"

    def test_writes_instructions_md(self, tmp_path):
        """Should write step-instructions.md."""
        write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"context": "test"},
        )

        instruction_file = tmp_path / "agent_steps" / "step_3_2" / "step-instructions.md"
        assert instruction_file.exists()

        content = instruction_file.read_text()
        assert "3.2" in content
        assert "step-output.json" in content
        assert "gmkit pdf-convert --resume" in content


class TestReadAgentOutput:
    """Test read_agent_output function."""

    def test_reads_output_envelope(self, tmp_path):
        """Should read and return output envelope."""
        step_dir = tmp_path / "agent_steps" / "step_3_2"
        step_dir.mkdir(parents=True)

        output_file = step_dir / "step-output.json"
        output_data = {
            "step_id": "3.2",
            "status": "success",
            "data": {"entries": []},
            "warnings": [],
        }
        output_file.write_text(json.dumps(output_data))

        envelope = read_agent_output("3.2", str(tmp_path), validate=False)

        assert envelope.step_id == "3.2"
        assert envelope.status == "success"

    def test_raises_on_missing_output(self, tmp_path):
        """Should raise error if output file not found."""
        with pytest.raises(AgentStepError) as exc_info:
            read_agent_output("3.2", str(tmp_path), validate=False)

        assert "Output file not found" in str(exc_info.value)

    def test_parses_rubric_scores(self, tmp_path):
        """Should parse rubric scores from output."""
        step_dir = tmp_path / "agent_steps" / "step_3_2"
        step_dir.mkdir(parents=True)

        output_file = step_dir / "step-output.json"
        output_data = {
            "step_id": "3.2",
            "status": "success",
            "data": {},
            "warnings": [],
            "rubric_scores": {"completeness": 5, "accuracy": 4},
        }
        output_file.write_text(json.dumps(output_data))

        envelope = read_agent_output("3.2", str(tmp_path), validate=False)

        assert envelope.rubric_scores["completeness"] == 5
        assert envelope.rubric_scores["accuracy"] == 4
