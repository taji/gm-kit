"""Unit tests for Phase 9 (Lint & Final Review).

Tests for markdown linting and quality checks.
"""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase9 import Phase9
from gm_kit.pdf_convert.state import ConversionState


def _write_required_quality_artifacts(output_dir):
    """Create required artifacts so high-critical quality steps can execute."""
    (output_dir / "tables-manifest.json").write_text(json.dumps({"tables": [], "total_count": 0}))
    (output_dir / "callout-rules.resolved.json").write_text(json.dumps([]))
    (output_dir / "font-family-mapping.json").write_text(
        json.dumps({"version": "1.0", "signatures": []})
    )


@pytest.fixture(autouse=True)
def mock_agent_step_runtime():
    """Mock AgentStepRuntime to prevent actual agent invocation in tests."""
    with patch("gm_kit.pdf_convert.agents.AgentStepRuntime") as mock_runtime_class:
        mock_runtime = MagicMock()
        mock_envelope = MagicMock()
        mock_envelope.data = {"score": 4, "issues": [], "ratings": {"overall": {"score": 4}}}
        mock_runtime.execute_step.return_value = (mock_envelope, MagicMock())
        mock_runtime_class.return_value = mock_runtime
        yield mock_runtime_class


class TestPhase9LintChecks:
    """Test markdown linting in Phase 9 using pymarkdownlnt."""

    @pytest.fixture
    def setup_phase9(self, tmp_path):
        """Create a Phase9 instance and mock state with input file."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        _write_required_quality_artifacts(tmp_path)
        return phase, state

    def test__should_report_success__when_no_violations(self, setup_phase9, tmp_path):
        """Test success report when no lint issues found."""
        phase, state = setup_phase9

        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("# Heading\n\nClean content without issues.\n\n- Item 1\n- Item 2")

        result = phase.execute(state)

        step_9_6 = [s for s in result.steps if s.step_id == "9.6"][0]
        assert step_9_6.status == PhaseStatus.SUCCESS
        assert step_9_6.message and "No lint violations found" in step_9_6.message

    def test__should_warn__when_lint_tool_unavailable(self, setup_phase9, tmp_path, monkeypatch):
        """Test explicit warning when linting cannot run."""
        phase, state = setup_phase9
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("# Heading\n\nContent")

        def _raise_not_found(*args, **kwargs):
            raise FileNotFoundError("python not found")

        monkeypatch.setattr("gm_kit.pdf_convert.phases.phase9.subprocess.run", _raise_not_found)

        result = phase.execute(state)

        step_9_6 = [s for s in result.steps if s.step_id == "9.6"][0]
        assert step_9_6.status == PhaseStatus.WARNING
        assert step_9_6.message and "Lint check skipped" in step_9_6.message
        assert "No lint violations found" not in step_9_6.message

    def test__should_use_current_interpreter__when_running_pymarkdown(
        self, setup_phase9, tmp_path, monkeypatch
    ):
        """Phase 9 should run pymarkdown via the active Python interpreter."""
        phase, state = setup_phase9
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("# Heading\n\nContent")
        captured_cmd: list[str] = []

        class _Proc:
            returncode = 0
            stdout = "[]"
            stderr = ""

        def _run(cmd, **_kwargs):
            captured_cmd[:] = cmd
            return _Proc()

        monkeypatch.setattr("gm_kit.pdf_convert.phases.phase9.subprocess.run", _run)

        result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS
        assert captured_cmd[:3] == [sys.executable, "-m", "pymarkdown"]


class TestPhase9AgentSteps:
    """Test that agent steps are properly executed."""

    @pytest.fixture
    def setup_phase9(self, tmp_path):
        """Create a Phase9 instance and mock state with input file."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        # Create input file
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("Content")
        _write_required_quality_artifacts(tmp_path)
        return phase, state

    def test__step_9_1_was_removed_from_architecture(self, setup_phase9):
        """Step 9.1 was removed - Phase 4 guarantees all page markers."""
        phase, state = setup_phase9
        result = phase.execute(state)

        # Step 9.1 should not exist
        step_9_1 = [s for s in result.steps if s.step_id == "9.1"]
        assert len(step_9_1) == 0

    def test__should_report_agent_step_9_2_executed(self, setup_phase9):
        """Test step 9.2 structural clarity assessment is executed via agent."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.2"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "AGENT" in step.description

    def test__should_report_agent_step_9_3_executed(self, setup_phase9):
        """Test step 9.3 text flow assessment is executed via agent."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.3"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "AGENT" in step.description

    def test__should_report_agent_step_9_4_status(self, setup_phase9):
        """Test step 9.4 table integrity check status."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.4"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "No tables found" in (step.message or "")
        assert "skipped (N/A)" in (step.message or "")

    def test__should_report_agent_step_9_5_status(self, setup_phase9):
        """Test step 9.5 callout formatting check status."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.5"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "AGENT" in step.description

    def test__should_report_agent_step_9_7_executed(self, setup_phase9):
        """Test step 9.7 TOC validation is executed via agent."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step_9_7 = [s for s in result.steps if s.step_id == "9.7"][0]
        assert step_9_7.status == PhaseStatus.SUCCESS
        assert "AGENT" in step_9_7.description

    def test__should_report_agent_step_9_8_executed(self, setup_phase9):
        """Test step 9.8 reading order review is executed via agent."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.8"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "AGENT" in step.description

    def test__should_fallback_score_from_rubric__when_data_score_missing(
        self, setup_phase9, mock_agent_step_runtime
    ):
        """When data.score is absent, score message should use rubric average."""
        phase, state = setup_phase9
        runtime = mock_agent_step_runtime.return_value

        def _execute(step_id, _inputs):
            envelope = MagicMock()
            if step_id == "9.3":
                envelope.data = {"flow_issues": [], "readability_score": 3}
                envelope.rubric_scores = {
                    "reading_order": 4,
                    "paragraph_integrity": 3,
                    "flow_continuity": 4,
                }
            else:
                envelope.data = {"score": 5}
                envelope.rubric_scores = {"overall": 5}
            return envelope, MagicMock()

        runtime.execute_step.side_effect = _execute

        result = phase.execute(state)
        step = [s for s in result.steps if s.step_id == "9.3"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert step.message == "Score: 4/5"


class TestPhase9UserSteps:
    """Test that user steps are properly stubbed."""

    @pytest.fixture
    def setup_phase9(self, tmp_path):
        """Create a Phase9 instance and mock state with input file."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        # Create input file
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("Content")
        _write_required_quality_artifacts(tmp_path)
        return phase, state

    def test__should_report_user_step_9_9_stubbed(self, setup_phase9):
        """Test step 9.9 present issues is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.9"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message
        assert "User" in step.message or "user" in step.message

    def test__should_report_user_step_9_10_stubbed(self, setup_phase9):
        """Test step 9.10 capture feedback is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.10"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_user_step_9_11_stubbed(self, setup_phase9):
        """Test step 9.11 apply corrections is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.11"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message


class TestPhase9EdgeCases:
    """Test edge cases and error handling in Phase 9."""

    def test__should_return_error__when_input_file_missing(self, tmp_path):
        """Test error when input file doesn't exist."""
        phase = Phase9()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert "Phase input file not found" in result.errors[0]

    def test__should_handle_empty_file(self, tmp_path):
        """Test handling of empty markdown file."""
        phase = Phase9()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("")
        _write_required_quality_artifacts(tmp_path)

        result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS
        step_9_6 = [s for s in result.steps if s.step_id == "9.6"][0]
        assert step_9_6.message and "No lint violations found" in step_9_6.message

    def test__should_handle_unicode_content(self, tmp_path):
        """Test handling of unicode content."""
        phase = Phase9()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("# 标题\n\n内容 with unicode 🎮")
        _write_required_quality_artifacts(tmp_path)

        result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS

    def test__phase9_has_agent_steps_property(self, tmp_path):
        """Test that has_agent_steps property returns True."""
        phase = Phase9()
        assert phase.has_agent_steps is True

    def test__phase9_has_user_steps_property(self, tmp_path):
        """Test that has_user_steps property returns True."""
        phase = Phase9()
        assert phase.has_user_steps is True

    def test__phase9_phase_num_is_9(self, tmp_path):
        """Test that phase_num property returns 9."""
        phase = Phase9()
        assert phase.phase_num == 9

    def test__should_have_unique_step_ids(self, tmp_path):
        """Ensure each step ID appears only once in phase output."""
        phase = Phase9()

        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)

        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("Content")
        _write_required_quality_artifacts(tmp_path)

        result = phase.execute(state)

        step_ids = [step.step_id for step in result.steps]
        assert len(step_ids) == len(set(step_ids))

    def test__should_return_structured_error__when_table_manifest_missing(self, tmp_path):
        """High-critical step 9.4 must fail with structured error when input is missing."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("Content")
        (tmp_path / "callout-rules.resolved.json").write_text(json.dumps([]))
        (tmp_path / "font-family-mapping.json").write_text(
            json.dumps({"version": "1.0", "signatures": []})
        )

        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.4"][0]
        assert step.status == PhaseStatus.ERROR
        payload = json.loads(step.message or "{}")
        assert payload["step_id"] == "9.4"
        assert "missing" in payload["error"].lower()
        assert "re-run previous phase" in payload["recovery"].lower()

    def test__should_return_structured_error__when_callout_config_missing(self, tmp_path):
        """High-critical step 9.5 must fail with structured error when input is missing."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
        input_path = tmp_path / "test-phase8.md"
        input_path.write_text("Content")
        (tmp_path / "tables-manifest.json").write_text(json.dumps({"tables": [], "total_count": 0}))
        (tmp_path / "font-family-mapping.json").write_text(
            json.dumps({"version": "1.0", "signatures": []})
        )

        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.5"][0]
        assert step.status == PhaseStatus.ERROR
        payload = json.loads(step.message or "{}")
        assert payload["step_id"] == "9.5"
        assert "missing" in payload["error"].lower()
        assert "re-run previous phase" in payload["recovery"].lower()
