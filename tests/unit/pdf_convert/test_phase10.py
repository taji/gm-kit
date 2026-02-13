"""Unit tests for Phase 10 (Report Generation).

Tests for conversion report generation and completion metadata.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.phase10 import PHASE_DETAILS, Phase10
from gm_kit.pdf_convert.state import ConversionState


class TestPhase10ReportGeneration:
    """Test conversion report generation in Phase 10."""

    @pytest.fixture
    def setup_phase10_with_phases(self, tmp_path):
        """Create a Phase10 instance with state that has completed phases."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[0, 1, 2, 3, 4],
            started_at="2026-02-10T10:00:00",
        )
        return phase, state

    @pytest.fixture
    def setup_phase10_with_empty_state(self, tmp_path):
        """Create a Phase10 instance with empty state."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[],
            started_at="2026-02-10T10:00:00",
        )
        return phase, state

    def test__should_generate_conversion_report__when_phases_completed(
        self, setup_phase10_with_phases, tmp_path
    ):
        """Test that conversion-report.md is generated."""
        phase, state = setup_phase10_with_phases

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        assert report_path.exists()
        assert result.status == PhaseStatus.SUCCESS

    def test__should_include_pdf_metadata_in_report(self, setup_phase10_with_phases, tmp_path):
        """Test that PDF metadata is included in report."""
        phase, state = setup_phase10_with_phases

        mock_metadata = MagicMock()
        mock_metadata.title = "Test PDF Title"
        mock_metadata.author = "Test Author"
        mock_metadata.page_count = 42

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = mock_metadata
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        assert "Test PDF Title" in report_content
        assert "Test Author" in report_content
        assert "42" in report_content

    def test__should_list_completed_phases_in_report(self, setup_phase10_with_phases, tmp_path):
        """Test that completed phases are listed in report."""
        phase, state = setup_phase10_with_phases

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        # Should list all completed phases
        assert "0" in report_content  # Phase 0
        assert "1" in report_content  # Phase 1
        assert "2" in report_content  # Phase 2

    def test__should_include_phase_details_in_report(self, setup_phase10_with_phases, tmp_path):
        """Test that phase details are included in report."""
        phase, state = setup_phase10_with_phases

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        # Check for phase names from PHASE_DETAILS
        assert "Pre-flight Analysis" in report_content or "Image Extraction" in report_content

    def test__should_include_performance_metrics(self, setup_phase10_with_phases, tmp_path):
        """Test that performance metrics are included."""
        phase, state = setup_phase10_with_phases

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        # Check for performance section
        assert "Performance" in report_content
        assert "Conversion Started" in report_content
        assert "Total Duration" in report_content

    def test__should_handle_missing_metadata_gracefully(self, setup_phase10_with_phases, tmp_path):
        """Test report generation when metadata is not available."""
        phase, state = setup_phase10_with_phases

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        # Should still generate report with unknown values
        assert "Unknown" in report_content or "conversion-report" in report_content.lower()


class TestPhase10CompletionMetadata:
    """Test completion metadata generation in Phase 10."""

    def test__should_create_completion_json_file(self, tmp_path):
        """Test that .completion.json is created."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1, 2, 3],
            started_at="2026-02-10T10:00:00",
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        completion_path = tmp_path / ".completion.json"
        assert completion_path.exists()

        with open(completion_path) as f:
            completion_data = json.load(f)

        assert "completed_at" in completion_data
        assert completion_data["total_phases"] == 3
        assert "warnings_count" in completion_data
        assert "errors_count" in completion_data

    def test__should_track_warnings_and_errors_from_state(self, tmp_path):
        """Test that warnings and errors from previous phases are tracked."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
            phase_results=[
                {
                    "phase_num": 1,
                    "warnings": ["Test warning 1", "Test warning 2"],
                    "errors": ["Test error 1"],
                }
            ],
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        completion_path = tmp_path / ".completion.json"
        with open(completion_path) as f:
            completion_data = json.load(f)

        assert completion_data["warnings_count"] == 2
        assert completion_data["errors_count"] == 1

        # Check report also includes warnings/errors
        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()
        assert "Test warning 1" in report_content
        assert "Test error 1" in report_content


class TestPhase10AgentSteps:
    """Test that agent steps are properly stubbed."""

    @pytest.fixture
    def setup_phase10(self, tmp_path):
        """Create a Phase10 instance with state."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
        )
        return phase, state

    def test__should_report_agent_step_10_2_stubbed(self, setup_phase10):
        """Test step 10.2 quality ratings is stubbed."""
        phase, state = setup_phase10

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "10.2"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message

    def test__should_report_agent_step_10_3_stubbed(self, setup_phase10):
        """Test step 10.3 document issues is stubbed."""
        phase, state = setup_phase10

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "10.3"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "Stub" in step.message


class TestPhase10Diagnostics:
    """Test diagnostics bundle handling in Phase 10."""

    @pytest.fixture
    def setup_phase10_with_diagnostics(self, tmp_path):
        """Create a Phase10 instance with diagnostics enabled."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
            diagnostics_enabled=True,
        )
        return phase, state

    @pytest.fixture
    def setup_phase10_without_diagnostics(self, tmp_path):
        """Create a Phase10 instance without diagnostics."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
            diagnostics_enabled=False,
        )
        return phase, state

    def test__should_report_diagnostics_step_success__when_enabled(
        self, setup_phase10_with_diagnostics
    ):
        """Test step 10.6 reports success when diagnostics enabled."""
        phase, state = setup_phase10_with_diagnostics

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "10.6"][0]
        assert step.status == PhaseStatus.SUCCESS
        assert "diagnostics" in step.message.lower()

    def test__should_report_diagnostics_step_skipped__when_disabled(
        self, setup_phase10_without_diagnostics
    ):
        """Test step 10.6 reports skipped when diagnostics not enabled."""
        phase, state = setup_phase10_without_diagnostics

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        step = [s for s in result.steps if s.step_id == "10.6"][0]
        assert step.status == PhaseStatus.SKIPPED


class TestPhase10EdgeCases:
    """Test edge cases in Phase 10."""

    def test__should_handle_empty_completed_phases(self, tmp_path):
        """Test report generation with no completed phases."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[],
            started_at="2026-02-10T10:00:00",
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        assert result.status == PhaseStatus.SUCCESS
        report_path = tmp_path / "conversion-report.md"
        assert report_path.exists()

    def test__should_handle_exception_during_report_generation(self, tmp_path):
        """Test error handling during report generation."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.side_effect = Exception("Metadata load failed")
            result = phase.execute(state)

        assert result.status == PhaseStatus.ERROR
        assert "Metadata load failed" in result.errors[0]

    def test__phase10_properties(self, tmp_path):
        """Test Phase 10 properties."""
        phase = Phase10()

        assert phase.phase_num == 10
        assert phase.has_agent_steps is True
        # Note: has_user_steps is not explicitly defined in Phase10,
        # might be inherited from base

    def test__should_set_output_file_in_result(self, tmp_path):
        """Test that output file path is set in result."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            result = phase.execute(state)

        expected_path = str(tmp_path / "conversion-report.md")
        assert result.output_file == expected_path

    def test__should_include_license_notice_in_report(self, tmp_path):
        """Test that license notice is included in report."""
        phase = Phase10()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=0,
            completed_phases=[1],
            started_at="2026-02-10T10:00:00",
        )

        with patch("gm_kit.pdf_convert.phases.phase10.load_metadata") as mock_load:
            mock_load.return_value = None
            phase.execute(state)

        report_path = tmp_path / "conversion-report.md"
        report_content = report_path.read_text()

        assert "License Notice" in report_content
        assert "copyrighted" in report_content.lower() or "Images" in report_content


class TestPhaseDetailsDictionary:
    """Test the PHASE_DETAILS dictionary."""

    def test__phase_details_should_have_all_phases(self):
        """Test that PHASE_DETAILS contains entries for all phases."""
        expected_phases = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        for phase_num in expected_phases:
            assert phase_num in PHASE_DETAILS, f"Phase {phase_num} missing from PHASE_DETAILS"

    def test__phase_details_should_have_required_fields(self):
        """Test that each phase entry has required fields."""
        required_fields = {"name", "changes", "outputs", "compare"}

        for phase_num, details in PHASE_DETAILS.items():
            assert required_fields.issubset(set(details.keys())), (
                f"Phase {phase_num} missing required fields"
            )

    def test__phase_10_details_should_be_complete(self):
        """Test that Phase 10 has correct details."""
        details = PHASE_DETAILS[10]

        assert "Report" in details["name"] or "Diagnostics" in details["name"]
        assert (
            "conversion-report" in details["outputs"].lower()
            or "report" in details["outputs"].lower()
        )
