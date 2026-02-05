"""Unit tests for orchestrator resume logic (T038) and copyright notice (T056)."""

from pathlib import Path

import pytest
from rich.console import Console

from gm_kit.pdf_convert.metadata import PDFMetadata
from gm_kit.pdf_convert.orchestrator import (
    Orchestrator,
    create_diagnostic_bundle,
    create_output_directory,
    generate_copyright_notice,
    insert_copyright_notice,
)
from gm_kit.pdf_convert.preflight import PreflightReport, TOCApproach, Complexity
from gm_kit.pdf_convert.state import ConversionState, ConversionStatus, save_state, load_state
from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.phases.base import PhaseStatus
from gm_kit.pdf_convert.phases.stubs import (
    MockPhaseConfig,
    MockPhaseRegistry,
)


class TestResumeLogic:
    """Tests for resume logic in orchestrator."""

    def test_resume__should_skip_completed_phases__when_resuming(self, tmp_path):
        """Resume skips phases that are already completed."""
        # Create a PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # Create state with phases 0-2 completed
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
            current_step="3.1",
            completed_phases=[0, 1, 2],
        )
        save_state(state)

        # Create mock phases that track execution
        executed_phases = []

        class TrackingPhase:
            def __init__(self, phase_num):
                self.phase_num = phase_num

            def execute(self, state):
                executed_phases.append(self.phase_num)
                from gm_kit.pdf_convert.phases.base import PhaseResult, PhaseStatus
                return PhaseResult(
                    phase_num=self.phase_num,
                    name=f"Phase {self.phase_num}",
                    status=PhaseStatus.SUCCESS,
                )

        mock_phases = [TrackingPhase(i) for i in range(11)]
        orchestrator = Orchestrator(phases=mock_phases)

        # Resume conversion
        exit_code = orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        # Should only execute phases 3-10 (not 0-2)
        assert 0 not in executed_phases
        assert 1 not in executed_phases
        assert 2 not in executed_phases
        assert 3 in executed_phases  # Should start from phase 3

    def test_resume__should_start_from_next_phase__when_phases_completed(self, tmp_path):
        """Resume starts from the phase after the last completed one."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # State with phases 0-3 completed, current at 4
        # (Not including phase 4 since it has output file requirement)
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=4,
            current_step="4.1",
            completed_phases=[0, 1, 2, 3],
        )
        save_state(state)

        executed_phases = []

        class TrackingPhase:
            def __init__(self, phase_num):
                self.phase_num = phase_num

            def execute(self, state):
                executed_phases.append(self.phase_num)
                from gm_kit.pdf_convert.phases.base import PhaseResult, PhaseStatus
                return PhaseResult(
                    phase_num=self.phase_num,
                    name=f"Phase {self.phase_num}",
                    status=PhaseStatus.SUCCESS,
                )

        mock_phases = [TrackingPhase(i) for i in range(11)]
        orchestrator = Orchestrator(phases=mock_phases)

        orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        # First executed phase should be 4
        assert executed_phases[0] == 4

    def test_resume__should_fail__when_output_file_missing(self, tmp_path):
        """Resume fails if completed phase output file is missing."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # State with phase 4 completed but no output file
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=5,
            current_step="5.1",
            completed_phases=[0, 1, 2, 3, 4],
        )
        save_state(state)

        # Phase 4 should have output file test-phase4.md, but we intentionally do not create it
        expected_output = tmp_path / "test-phase4.md"
        assert not expected_output.exists()
        orchestrator = Orchestrator()

        exit_code = orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        # Should fail with STATE_ERROR due to missing output
        assert exit_code == ExitCode.STATE_ERROR

    def test_resume__should_warn__when_state_left_in_progress(self, tmp_path, capsys):
        """Resume warns when state was left in_progress."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # State stuck in IN_PROGRESS
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
            current_step="3.1",
            completed_phases=[0, 1, 2],
            status=ConversionStatus.IN_PROGRESS,
        )
        save_state(state)

        # Use mock phases to avoid actual execution
        from gm_kit.pdf_convert.phases.stubs import get_mock_phases
        orchestrator = Orchestrator(phases=get_mock_phases())

        orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        captured = capsys.readouterr()
        # Expect: "WARNING: Previous conversion appears to have been interrupted. Resuming from last completed step."
        assert (
            "WARNING: Previous conversion appears to have been interrupted. Resuming from \n"
            "last completed step.\n"
        ) in captured.out


class TestMissingStateFile:
    """Tests for missing state file handling."""

    def test_resume__should_fail__when_no_state_file(self, tmp_path):
        """Resume fails when no .state.json exists."""
        orchestrator = Orchestrator()

        exit_code = orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        assert exit_code == ExitCode.STATE_ERROR


class TestCorruptStateFile:
    """Tests for corrupt state file handling."""

    def test_resume__should_fail__when_invalid_json(self, tmp_path):
        """Resume fails when state file contains invalid JSON."""
        (tmp_path / ".state.json").write_text("not valid json{")

        orchestrator = Orchestrator()
        exit_code = orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        assert exit_code == ExitCode.STATE_ERROR

    def test_resume__should_fail__when_missing_fields(self, tmp_path):
        """Resume fails when state file is missing required fields."""
        (tmp_path / ".state.json").write_text('{"version": "1.0"}')

        orchestrator = Orchestrator()
        exit_code = orchestrator.resume_conversion(tmp_path, auto_proceed=True)

        assert exit_code == ExitCode.STATE_ERROR


class TestReRunSinglePhase:
    """Tests for re-running a single phase."""

    def test_rerun_phase__should_fail__when_prerequisites_missing(self, tmp_path):
        """Re-running phase N requires phases 0..N-1 to be completed."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # State with only phase 0 completed
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=1,
            current_step="1.1",
            completed_phases=[0],
        )
        save_state(state)

        orchestrator = Orchestrator()

        # Try to run phase 5 without completing 1-4
        exit_code = orchestrator.run_single_phase(tmp_path, phase_num=5)

        assert exit_code == ExitCode.STATE_ERROR

    def test_rerun_phase__should_succeed__when_phase_zero(self, tmp_path):
        """Phase 0 can be re-run without prerequisites."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=5,
            current_step="5.1",
            completed_phases=[0, 1, 2, 3, 4],
        )
        save_state(state)

        from gm_kit.pdf_convert.phases.stubs import get_mock_phases
        orchestrator = Orchestrator(phases=get_mock_phases())

        # Phase 0 should work
        exit_code = orchestrator.run_single_phase(tmp_path, phase_num=0)

        assert exit_code == ExitCode.SUCCESS


class TestFromStepResume:
    """Tests for resuming from a specific step."""

    def test_from_step__should_reject__when_invalid_format(self, tmp_path):
        """--from-step rejects invalid step format."""
        orchestrator = Orchestrator()

        # Invalid format
        exit_code = orchestrator.run_from_step(tmp_path, step_id="invalid")
        assert exit_code == ExitCode.FILE_ERROR

        exit_code = orchestrator.run_from_step(tmp_path, step_id="5")
        assert exit_code == ExitCode.FILE_ERROR

        exit_code = orchestrator.run_from_step(tmp_path, step_id="5.3.1")
        assert exit_code == ExitCode.FILE_ERROR

    def test_from_step__should_reject__when_invalid_phase_range(self, tmp_path):
        """--from-step rejects steps in invalid phase range."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
        )
        save_state(state)

        orchestrator = Orchestrator()

        # Phase 11 doesn't exist
        exit_code = orchestrator.run_from_step(tmp_path, step_id="11.1")
        assert exit_code == ExitCode.FILE_ERROR


class TestShowStatus:
    """Tests for show_status command (T051)."""

    def test_status__should_return_success__when_no_state(self, tmp_path, capsys):
        """--status with no state file shows message and returns success."""
        orchestrator = Orchestrator()

        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()
        # Expect: "No conversion in progress in this directory."
        assert "No conversion in progress in this directory." in captured.out

    def test_status__should_show_phase_info__when_phases_completed(self, tmp_path, capsys):
        """--status shows phase completion information."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=5,
            current_step="5.3",
            completed_phases=[0, 1, 2, 3, 4],
        )
        save_state(state)

        orchestrator = Orchestrator()
        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()

        # Expect: "Conversion Status: <output_dir>"
        assert f"Conversion Status: {tmp_path.resolve()}" in captured.out
        # Expect: "Status: in_progress"
        assert "Status: in_progress" in captured.out
        # Expect: "Phase  Name  Status  Completed" header
        phase_header = f"{'Phase':<6} {'Name':<24} {'Status':<12} {'Completed'}"
        assert phase_header in captured.out

    def test_status__should_show_in_progress__when_status_in_progress(self, tmp_path, capsys):
        """--status shows in_progress status correctly per FR-009a."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=6,
            current_step="6.2",
            completed_phases=[0, 1, 2, 3, 4, 5],
            status=ConversionStatus.IN_PROGRESS,
        )
        save_state(state)

        orchestrator = Orchestrator()
        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()

        # Expect: "Status: in_progress"
        assert "Status: in_progress" in captured.out
        # Expect: "6 Structural Formatting in_progress (step 6.2)"
        expected_line = f"{6:<6} {'Structural Formatting':<24} {'in_progress (step 6.2)':<12}"
        assert expected_line in captured.out

    def test_status__should_show_completed__when_all_phases_done(self, tmp_path, capsys):
        """--status shows completed status correctly per FR-009a."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=10,
            current_step="10.5",
            completed_phases=list(range(11)),  # All phases completed
            status=ConversionStatus.COMPLETED,
        )
        save_state(state)

        orchestrator = Orchestrator()
        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()

        # Expect: "Status: completed"
        assert "Status: completed" in captured.out

    def test_status__should_show_error_info__when_status_failed(self, tmp_path, capsys):
        """--status shows failed status with error info per FR-009a."""
        from gm_kit.pdf_convert.state import ErrorInfo

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        error = ErrorInfo(
            phase=5,
            step="5.3",
            code="TEST_ERROR",
            message="Test error message",
            recoverable=True,
            suggestion="Try re-running phase 5",
        )

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=5,
            current_step="5.3",
            completed_phases=[0, 1, 2, 3, 4],
            status=ConversionStatus.FAILED,
            error=error,
        )
        save_state(state)

        orchestrator = Orchestrator()
        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()

        # Expect: "Status: failed"
        assert "Status: failed" in captured.out
        # Expect: "Error: Test error message"
        assert "Error: Test error message" in captured.out
        # Expect: "Suggestion: Try re-running phase 5"
        assert "Suggestion: Try re-running phase 5" in captured.out

    def test_status__should_show_pdf_info__when_state_exists(self, tmp_path, capsys):
        """--status shows source PDF name and size per FR-009a."""
        pdf_path = tmp_path / "my-document.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content" * 1000)  # ~21KB

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=3,
            current_step="3.1",
            completed_phases=[0, 1, 2],
        )
        save_state(state)

        orchestrator = Orchestrator()
        exit_code = orchestrator.show_status(tmp_path)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()

        # Expect: "Source: my-document.pdf (<size> MB)"
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"
        assert f"Source: my-document.pdf ({size_str})" in captured.out


class TestCopyrightNotice:
    """Tests for copyright notice generation (T056)."""

    def test_copyright_notice__should_generate_template__when_valid_metadata(self):
        """Copyright notice uses correct template format per FR-050a."""
        from gm_kit.pdf_convert.metadata import PDFMetadata

        metadata = PDFMetadata(
            title="The Adventure Module",
            author="Game Master Publishing",
            creator="PDF Creator",
            producer="PDF Producer",
            copyright="(c) 2024 Game Master Publishing",
            page_count=50,
            file_size_bytes=1024000,
        )

        notice = generate_copyright_notice(metadata)

        # Should be HTML comment
        assert notice.startswith("<!--")
        assert "-->" in notice
        # Should include title
        assert "The Adventure Module" in notice
        # Should include author
        assert "Game Master Publishing" in notice
        # Should include copyright
        assert "(c) 2024 Game Master Publishing" in notice
        # Should include tool attribution
        assert "GM-Kit" in notice

    def test_copyright_notice__should_use_fallbacks__when_metadata_empty(self):
        """Copyright notice uses fallbacks for missing metadata."""
        from gm_kit.pdf_convert.metadata import PDFMetadata

        metadata = PDFMetadata(
            title="",  # Empty title
            author="",  # Empty author
            creator="",  # Empty creator
            producer="",
            copyright="",  # Empty copyright
            page_count=10,
            file_size_bytes=1000,
        )

        notice = generate_copyright_notice(metadata)

        # Should still be valid HTML comment
        assert notice.startswith("<!--")
        assert "-->" in notice
        # Should have fallback for author
        assert "Unknown" in notice
        # Should have fallback for copyright
        assert "See original publication" in notice

    def test_copyright_notice__should_use_creator__when_author_empty(self):
        """Copyright notice uses creator when author is empty."""
        from gm_kit.pdf_convert.metadata import PDFMetadata

        metadata = PDFMetadata(
            title="Test Document",
            author="",  # Empty
            creator="Document Creator Inc",
            producer="",
            copyright="",
            page_count=10,
            file_size_bytes=1000,
        )

        notice = generate_copyright_notice(metadata)

        # Should use creator as fallback
        assert "Document Creator Inc" in notice

    def test_copyright_notice__should_insert_at_beginning__when_file_exists(self, tmp_path):
        """Copyright notice inserted at beginning of file per FR-049a."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading 1\n\nSome content here.\n")

        notice = "<!-- COPYRIGHT NOTICE -->\n\n"
        insert_copyright_notice(md_file, notice)

        content = md_file.read_text()

        # Notice should be at the very beginning
        assert content.startswith("<!-- COPYRIGHT NOTICE -->")
        # Original content should follow
        assert "# Heading 1" in content
        assert "Some content here" in content

    def test_copyright_notice__should_preserve_content__when_inserted(self, tmp_path):
        """Copyright notice insertion preserves all original content."""
        original_content = """# Chapter 1

This is the introduction.

## Section 1.1

More content here with **bold** and *italic*.

- List item 1
- List item 2
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(original_content)

        notice = "<!-- Notice -->\n\n"
        insert_copyright_notice(md_file, notice)

        content = md_file.read_text()

        # All original content should be present
        assert "# Chapter 1" in content
        assert "This is the introduction" in content
        assert "## Section 1.1" in content
        assert "**bold**" in content
        assert "- List item 1" in content


class TestPhaseFailure:
    """Tests for phase failure handling during orchestration."""

    def _make_orchestrator_with_phases(self, registry):
        """Create an orchestrator using a custom mock phase registry."""
        return Orchestrator(phases=registry.get_all_phases())

    def test_phase_failure__should_stop_pipeline__when_phase_returns_error(self, tmp_path, capsys):
        """Pipeline stops when a phase returns ERROR status."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        # Create state with phase 0 completed, ready for phase 1+
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            current_phase=1,
            current_step="1.1",
            completed_phases=[0],
        )
        save_state(state)

        # Configure phase 3 to fail
        registry = MockPhaseRegistry()
        registry.configure_error(3, "Font extraction failed: corrupt font table")
        orchestrator = self._make_orchestrator_with_phases(registry)

        exit_code = orchestrator._run_phases(state, start_phase=1)

        assert exit_code == ExitCode.PDF_ERROR

        # State should reflect failure
        saved_state = load_state(tmp_path)
        assert saved_state.status == ConversionStatus.FAILED
        assert saved_state.error is not None
        assert "font extraction" in saved_state.error.message.lower()

    def test_phase_failure__should_record_suggestion__when_phase_returns_error(self, tmp_path, capsys):
        """Failed phase records a re-run suggestion in state."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            completed_phases=[0],
        )
        save_state(state)

        registry = MockPhaseRegistry()
        registry.configure_error(2, "Image removal failed")
        orchestrator = self._make_orchestrator_with_phases(registry)

        orchestrator._run_phases(state, start_phase=1)

        saved_state = load_state(tmp_path)
        assert saved_state.error.suggestion is not None
        assert "--phase 2" in saved_state.error.suggestion

    def test_phase_failure__should_skip_later_phases__when_phase_returns_error(self, tmp_path, capsys):
        """Phases after the failed phase are not executed."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            completed_phases=[0],
        )
        save_state(state)

        registry = MockPhaseRegistry()
        registry.configure_error(3, "Phase 3 failed")
        orchestrator = self._make_orchestrator_with_phases(registry)

        orchestrator._run_phases(state, start_phase=1)

        saved_state = load_state(tmp_path)
        # Phases 1 and 2 should be completed, but not 3+
        assert 1 in saved_state.completed_phases
        assert 2 in saved_state.completed_phases
        assert 3 not in saved_state.completed_phases
        assert 4 not in saved_state.completed_phases

    def test_phase_failure__should_capture_step_info__when_step_fails(self, tmp_path, capsys):
        """Failure at a specific step is captured in state."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            completed_phases=[0, 1, 2, 3, 4],
        )
        save_state(state)

        registry = MockPhaseRegistry()
        registry.configure(5, MockPhaseConfig(
            status=PhaseStatus.ERROR,
            error_message="Bad character at offset 4092",
            fail_at_step=2,
        ))
        orchestrator = self._make_orchestrator_with_phases(registry)

        exit_code = orchestrator._run_phases(state, start_phase=5)

        assert exit_code == ExitCode.PDF_ERROR
        saved_state = load_state(tmp_path)
        assert saved_state.status == ConversionStatus.FAILED
        assert "4092" in saved_state.error.message

    def test_phase_failure__should_continue_pipeline__when_phase_returns_warning(self, tmp_path, capsys):
        """Pipeline continues when a phase returns WARNING status."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            completed_phases=[0],
        )
        save_state(state)

        registry = MockPhaseRegistry()
        registry.configure_warning(3, "Low confidence font mapping detected")
        orchestrator = self._make_orchestrator_with_phases(registry)

        exit_code = orchestrator._run_phases(state, start_phase=1)

        assert exit_code == ExitCode.SUCCESS

        # All phases should have completed
        saved_state = load_state(tmp_path)
        assert saved_state.status == ConversionStatus.COMPLETED
        for i in range(1, 11):
            assert i in saved_state.completed_phases

    def test_phase_failure__should_display_warning__when_phase_returns_warning(self, tmp_path, capsys):
        """Warning message from a phase is displayed to user."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(tmp_path),
            completed_phases=[0],
        )
        save_state(state)

        registry = MockPhaseRegistry()
        registry.configure_warning(5, "3 images could not be extracted")
        orchestrator = self._make_orchestrator_with_phases(registry)

        orchestrator._run_phases(state, start_phase=1)

        captured = capsys.readouterr()
        # Expect: "WARNING: 3 images could not be extracted"
        assert "WARNING: 3 images could not be extracted" in captured.out


class TestOutputDirectory:
    """Tests for output directory creation."""

    def test_create_output_dir__should_raise_permission_error__when_mkdir_fails(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Permission errors are surfaced with formatted message."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        def _raise_permission(*_args, **_kwargs):
            raise PermissionError("denied")

        monkeypatch.setattr(Path, "mkdir", _raise_permission)

        with pytest.raises(PermissionError) as excinfo:
            create_output_directory(pdf_path)

        assert "Cannot create output directory" in str(excinfo.value)


class TestDiagnosticBundle:
    """Tests for diagnostic bundle creation."""

    def test_diagnostic_bundle__should_return_none__when_disabled(self, tmp_path):
        """Diagnostics disabled returns None."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            diagnostics_enabled=False,
        )
        assert create_diagnostic_bundle(state) is None

    def test_diagnostic_bundle__should_return_none__when_zip_fails(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Zip failures return None without raising."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
            diagnostics_enabled=True,
        )

        class _FailingZip:
            def __init__(self, *_args, **_kwargs):
                raise OSError("zip failed")

        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.zipfile.ZipFile", _FailingZip)
        assert create_diagnostic_bundle(state, console=Console()) is None


class TestRunNewConversion:
    """Tests for new conversion paths."""

    def test_run_new_conversion__should_return_file_error__when_pdf_missing(self, tmp_path):
        """Missing PDFs return FILE_ERROR."""
        orchestrator = Orchestrator()
        exit_code = orchestrator.run_new_conversion(tmp_path / "missing.pdf")
        assert exit_code == ExitCode.FILE_ERROR

    def test_run_new_conversion__should_return_file_error__when_pdf_unreadable(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Permission errors return FILE_ERROR."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")

        def _raise_permission(*_args, **_kwargs):
            raise PermissionError("denied")

        monkeypatch.setattr("builtins.open", _raise_permission)
        orchestrator = Orchestrator()
        exit_code = orchestrator.run_new_conversion(pdf_path)
        assert exit_code == ExitCode.FILE_ERROR

    def test_run_new_conversion__should_delegate__when_state_exists(self, tmp_path, monkeypatch):
        """Existing state delegates to handler."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
        )
        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.create_output_directory",
            lambda *_a, **_k: output_dir,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.load_state", lambda *_a, **_k: state)

        orchestrator = Orchestrator()
        called = {"delegated": False}

        def _handle_existing_state(*_a, **_k):
            called["delegated"] = True
            return ExitCode.SUCCESS

        monkeypatch.setattr(
            orchestrator,
            "_handle_existing_state",
            _handle_existing_state,
        )

        exit_code = orchestrator.run_new_conversion(pdf_path)
        assert exit_code == ExitCode.SUCCESS
        assert called["delegated"] is True

    def test_run_new_conversion__should_return_pdf_error__when_encrypted(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Encrypted PDFs return PDF_ERROR."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.create_output_directory",
            lambda *_a, **_k: output_dir,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.load_state", lambda *_a, **_k: None)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.extract_metadata",
            lambda *_a, **_k: (_ for _ in ()).throw(ValueError("encrypted")),
        )

        orchestrator = Orchestrator()
        exit_code = orchestrator.run_new_conversion(pdf_path)
        assert exit_code == ExitCode.PDF_ERROR

    def test_run_new_conversion__should_return_pdf_error__when_scanned_pdf(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Scanned PDFs return PDF_ERROR."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        metadata = PDFMetadata(page_count=1, file_size_bytes=1024)
        report = PreflightReport(
            pdf_name=pdf_path.name,
            file_size_display="1.0 KB",
            page_count=1,
            image_count=0,
            text_extractable=False,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )

        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.create_output_directory",
            lambda *_a, **_k: output_dir,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.load_state", lambda *_a, **_k: None)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.extract_metadata", lambda *_a, **_k: metadata)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.save_metadata", lambda *_a, **_k: None)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.analyze_pdf", lambda *_a, **_k: report)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.display_preflight_report",
            lambda *_a, **_k: None,
        )

        orchestrator = Orchestrator()
        exit_code = orchestrator.run_new_conversion(pdf_path)
        assert exit_code == ExitCode.PDF_ERROR

    def test_run_new_conversion__should_return_user_abort__when_user_cancels(
        self,
        tmp_path,
        monkeypatch,
    ):
        """User cancellation returns USER_ABORT."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        metadata = PDFMetadata(page_count=1, file_size_bytes=1024)
        report = PreflightReport(
            pdf_name=pdf_path.name,
            file_size_display="1.0 KB",
            page_count=1,
            image_count=0,
            text_extractable=True,
            toc_approach=TOCApproach.NONE,
            font_complexity=Complexity.LOW,
            overall_complexity=Complexity.LOW,
        )

        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.create_output_directory",
            lambda *_a, **_k: output_dir,
        )
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.load_state", lambda *_a, **_k: None)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.extract_metadata", lambda *_a, **_k: metadata)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.save_metadata", lambda *_a, **_k: None)
        monkeypatch.setattr("gm_kit.pdf_convert.orchestrator.analyze_pdf", lambda *_a, **_k: report)
        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.display_preflight_report",
            lambda *_a, **_k: None,
        )
        monkeypatch.setattr(
            "gm_kit.pdf_convert.orchestrator.prompt_user_confirmation",
            lambda *_a, **_k: False,
        )

        orchestrator = Orchestrator()
        exit_code = orchestrator.run_new_conversion(pdf_path)
        assert exit_code == ExitCode.USER_ABORT


class TestRunSinglePhase:
    """Tests for run_single_phase error paths."""

    def test_run_single_phase__should_return_state_error__when_phase_missing(self, tmp_path):
        """Missing phase returns STATE_ERROR."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        class _Phase:
            def __init__(self, phase_num):
                self.phase_num = phase_num

        orchestrator = Orchestrator(phases=[_Phase(1)])
        exit_code = orchestrator._run_single_phase(state, phase_num=0)
        assert exit_code == ExitCode.STATE_ERROR

    def test_run_single_phase__should_return_pdf_error__when_phase_raises(
        self,
        tmp_path,
    ):
        """Exceptions in phase execution return PDF_ERROR."""
        state = ConversionState(
            pdf_path=str(tmp_path / "test.pdf"),
            output_dir=str(tmp_path),
        )

        class _Phase:
            def __init__(self, phase_num):
                self.phase_num = phase_num

            def execute(self, _state):
                raise RuntimeError("boom")

        orchestrator = Orchestrator(phases=[_Phase(0)])
        exit_code = orchestrator._run_single_phase(state, phase_num=0)
        assert exit_code == ExitCode.PDF_ERROR
