"""Tests for workspace I/O helpers."""

import json

import pytest

from gm_kit.pdf_convert.agents.agent_step import (
    read_agent_output,
    write_agent_inputs,
)
from gm_kit.pdf_convert.agents.errors import AgentStepError
from gm_kit.pdf_convert.step_identity import StepIdentity


def _step_identity(step_id: str) -> StepIdentity:
    identities = {
        "3.2": StepIdentity(
            step_key="parse-visual-toc-page",
            display_id="3.2",
            display_name="Parse visual TOC page",
            phase=3,
        ),
        "4.5": StepIdentity(
            step_key="resolve-split-sentences-at-chunk-boundaries",
            display_id="4.5",
            display_name="Resolve split sentences at chunk boundaries",
            phase=4,
        ),
    }
    return identities[step_id]


class TestWriteAgentInputs:
    """Test write_agent_inputs function."""

    def test_uses_registry_step_key_for_workspace_path(self, tmp_path, monkeypatch):
        """Should build workspace paths from the registry's stable step key."""

        class _StepDef:
            step_key = "stable-step-key"
            description = "Human-friendly display text"
            phase = 9

        class _Registry:
            def get(self, _step_id):
                return _StepDef()

        monkeypatch.setattr(
            "gm_kit.pdf_convert.agents.agent_step.get_registry",
            lambda: _Registry(),
        )

        step_dir = write_agent_inputs(
            step_id="9.3",
            workspace=str(tmp_path),
            inputs={"test": "data"},
        )

        assert step_dir == tmp_path / "agent_steps" / "phase_9" / "stable-step-key"

    def test_creates_step_directory(self, tmp_path):
        """Should create step directory structure."""
        step_dir = write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"test": "data"},
        )

        assert step_dir.exists()
        assert step_dir == _step_identity("3.2").workspace_path(tmp_path)
        assert step_dir.parent.name == "phase_3"
        assert step_dir.parent.parent == tmp_path / "agent_steps"

    def test_writes_input_json(self, tmp_path):
        """Should write step-input.json."""
        write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"toc_text": "sample"},
        )

        input_file = _step_identity("3.2").workspace_path(tmp_path) / "step-input.json"
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

        instruction_file = _step_identity("3.2").workspace_path(tmp_path) / "step-instructions.md"
        assert instruction_file.exists()

        content = instruction_file.read_text()
        assert "3.2" in content
        assert "step-output.json" in content
        assert "gmkit pdf-convert --resume" not in content

    def test_clears_stale_output_file(self, tmp_path):
        """Should remove stale step-output.json when creating a new handoff."""
        step_dir = _step_identity("3.2").workspace_path(tmp_path)
        step_dir.mkdir(parents=True)
        output_file = step_dir / "step-output.json"
        output_file.write_text('{"status":"success"}', encoding="utf-8")

        write_agent_inputs(
            step_id="3.2",
            workspace=str(tmp_path),
            inputs={"context": "fresh-run"},
        )

        assert not output_file.exists()

    def test_copies_schema_into_workspace(self, tmp_path):
        """Should materialize step schema under workspace/schemas."""
        write_agent_inputs(
            step_id="4.5",
            workspace=str(tmp_path),
            inputs={"context": "schema-check"},
        )

        schema_file = tmp_path / "schemas" / "step_4_5.schema.json"
        assert schema_file.exists()

    def test_sets_default_output_contract_when_missing(self, tmp_path):
        """Should set output_contract in step-input when caller omits it."""
        write_agent_inputs(
            step_id="4.5",
            workspace=str(tmp_path),
            inputs={"context": "contract-check"},
        )

        input_file = _step_identity("4.5").workspace_path(tmp_path) / "step-input.json"
        data = json.loads(input_file.read_text(encoding="utf-8"))
        assert data["output_contract"] == "schemas/step_4_5.schema.json"

    def test_logs_warning_when_defaulting_output_contract(self, tmp_path, caplog):
        """Should warn when fallback output_contract is used."""
        with caplog.at_level("WARNING"):
            write_agent_inputs(
                step_id="4.5",
                workspace=str(tmp_path),
                inputs={"context": "contract-check"},
            )

        assert "Missing output_contract in step payload for 4.5" in caplog.text


class TestReadAgentOutput:
    """Test read_agent_output function."""

    def test_reads_output_envelope(self, tmp_path):
        """Should read and return output envelope."""
        step_dir = _step_identity("3.2").workspace_path(tmp_path)
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
        step_dir = _step_identity("3.2").workspace_path(tmp_path)
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
