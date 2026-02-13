"""Unit tests for Phase 9 (Lint & Final Review).

Tests for markdown linting and quality checks.
"""

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase9 import Phase9
from gm_kit.pdf_convert.state import ConversionState


class TestPhase9LintChecks:
    """Test markdown linting in Phase 9 using pymarkdownlnt."""

    @pytest.fixture
    def setup_phase9(self, tmp_path):
        """Create a Phase9 instance and mock state with input file."""
        phase = Phase9()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(pdf_path=str(pdf_path), output_dir=str(tmp_path), current_phase=0)
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


class TestPhase9AgentSteps:
    """Test that agent steps are properly stubbed."""

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
        return phase, state

    def test__should_report_agent_step_9_1_stubbed(self, setup_phase9):
        """Test step 9.1 completeness check is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.1"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_2_stubbed(self, setup_phase9):
        """Test step 9.2 structure validation is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.2"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_3_stubbed(self, setup_phase9):
        """Test step 9.3 reading flow check is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.3"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_4_stubbed(self, setup_phase9):
        """Test step 9.4 table formatting check is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.4"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_5_stubbed(self, setup_phase9):
        """Test step 9.5 callout formatting check is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.5"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_7_stubbed(self, setup_phase9):
        """Test step 9.7 TOC validation is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.7"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_9_8_stubbed(self, setup_phase9):
        """Test step 9.8 two-column review is stubbed."""
        phase, state = setup_phase9
        result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "9.8"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message


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

        result = phase.execute(state)

        step_ids = [step.step_id for step in result.steps]
        assert len(step_ids) == len(set(step_ids))
