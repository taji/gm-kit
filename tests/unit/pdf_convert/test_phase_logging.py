"""Tests for Phase base class logging methods (E4-07a-i)."""

import re

from gm_kit.pdf_convert.phases.base import Phase, PhaseResult, PhaseStatus, StepResult
from gm_kit.pdf_convert.state import ConversionState


class SimpleTestPhase(Phase):
    """Simple test phase for testing logging methods."""

    def __init__(self, phase_num: int = 1) -> None:
        self._phase_num = phase_num

    @property
    def phase_num(self) -> int:
        return self._phase_num

    def execute(self, state: ConversionState) -> PhaseResult:
        return self.create_result()


class TestPhaseLogging:
    """Tests for Phase logging methods."""

    def test_log_phase_start_creates_horizontal_header(self, tmp_path):
        """_log_phase_start should create header with horizontal lines."""
        phase = SimpleTestPhase(phase_num=3)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        phase._log_phase_start(output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        # Should have horizontal divider lines (box drawing character ─)
        lines = content.strip().split("\n")
        assert lines[0].startswith("─")
        assert lines[-1].startswith("─")

        # Should have phase info
        assert "Phase 3" in content
        assert "Started:" in content

        # Should have ISO8601 timestamp
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", content)

    def test_log_phase_start_handles_missing_directory_gracefully(self, tmp_path):
        """_log_phase_start should handle missing output directory."""
        phase = SimpleTestPhase()
        nonexistent_dir = tmp_path / "nonexistent"

        # Should not raise
        phase._log_phase_start(nonexistent_dir)

    def test_log_step_success(self, tmp_path):
        """_log_step should log successful step with checkmark."""
        phase = SimpleTestPhase(phase_num=1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        step = StepResult(
            step_id="1.1",
            description="Test step",
            status=PhaseStatus.SUCCESS,
            duration_ms=150,
            message="Step completed",
        )

        phase._log_step(step, output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        # Should have success indicator
        assert "✓" in content
        assert "Step 1.1" in content
        assert "Test step" in content
        assert "SUCCESS" in content
        assert "Step completed" in content
        assert "150ms" in content

    def test_log_step_warning(self, tmp_path):
        """_log_step should log warning step with warning symbol."""
        phase = SimpleTestPhase(phase_num=2)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        step = StepResult(
            step_id="2.3",
            description="Warning step",
            status=PhaseStatus.WARNING,
            duration_ms=45,
            message="Something might be wrong",
        )

        phase._log_step(step, output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        assert "⚠" in content
        assert "WARNING" in content
        assert "Something might be wrong" in content

    def test_log_step_error(self, tmp_path):
        """_log_step should log error step with error symbol."""
        phase = SimpleTestPhase(phase_num=3)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        step = StepResult(
            step_id="3.5",
            description="Error step",
            status=PhaseStatus.ERROR,
            duration_ms=10,
            message="Step failed",
        )

        phase._log_step(step, output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        assert "✗" in content
        assert "ERROR" in content
        assert "Step failed" in content

    def test_log_step_skipped(self, tmp_path):
        """_log_step should log skipped step with skip symbol."""
        phase = SimpleTestPhase(phase_num=4)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        step = StepResult(
            step_id="4.2",
            description="Skipped step",
            status=PhaseStatus.SKIPPED,
            duration_ms=0,
            message="Not needed",
        )

        phase._log_step(step, output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        assert "⏸" in content
        assert "SKIPPED" in content
        assert "Not needed" in content

    def test_log_step_no_message(self, tmp_path):
        """_log_step should handle step with no message."""
        phase = SimpleTestPhase(phase_num=1)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        step = StepResult(
            step_id="1.2",
            description="Step without message",
            status=PhaseStatus.SUCCESS,
            duration_ms=100,
            message=None,
        )

        phase._log_step(step, output_dir)

        log_path = output_dir / "conversion.log"
        content = log_path.read_text(encoding="utf-8")

        # Should show "N/A" for missing message
        assert "N/A" in content

    def test_log_step_handles_missing_directory_gracefully(self, tmp_path):
        """_log_step should handle missing output directory."""
        phase = SimpleTestPhase()
        nonexistent_dir = tmp_path / "nonexistent"

        step = StepResult(
            step_id="1.1",
            description="Test step",
            status=PhaseStatus.SUCCESS,
        )

        # Should not raise
        phase._log_step(step, nonexistent_dir)
