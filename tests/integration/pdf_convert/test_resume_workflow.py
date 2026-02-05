"""Integration tests for resume workflow (T039)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from gm_kit.pdf_convert.errors import ErrorMessages, format_error


# Test PDF path
TEST_PDF_PATH = Path(__file__).parent.parent.parent.parent / (
    "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf"
)


@pytest.fixture
def gmkit_cli():
    """Get command to run gmkit CLI."""
    return [sys.executable, "-m", "gm_kit.cli"]


@pytest.fixture
def src_path():
    """Get absolute path to src directory."""
    return str(Path(__file__).parent.parent.parent.parent / "src")


def create_partial_state(output_dir: Path, pdf_path: Path, completed_phases: list):
    """Create a partial state file simulating interrupted conversion."""
    from datetime import datetime

    state = {
        "version": "1.0",
        "pdf_path": str(pdf_path.resolve()),
        "output_dir": str(output_dir.resolve()),
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "current_phase": max(completed_phases) + 1 if completed_phases else 0,
        "current_step": f"{max(completed_phases) + 1 if completed_phases else 0}.1",
        "completed_phases": completed_phases,
        "phase_results": [],
        "status": "in_progress",
        "error": None,
        "diagnostics_enabled": False,
        "config": {},
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".state.json").write_text(json.dumps(state, indent=2))

    # Create minimal metadata
    metadata = {
        "page_count": 10,
        "file_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 1000,
        "title": "Test Document",
        "author": "",
        "creator": "",
        "producer": "",
        "has_toc": False,
        "toc_entries": 0,
        "toc_max_depth": 0,
        "image_count": 0,
        "font_count": 2,
        "extracted_at": datetime.now().isoformat(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


class TestResumeInterruptedConversion:
    """Tests for resuming interrupted conversion."""

    def test_resume_workflow__should_continue__when_checkpoint_exists(self, tmp_path, gmkit_cli, src_path):
        """--resume continues from last completed phase."""
        output_dir = tmp_path / "output"

        # Create state simulating interruption at phase 3
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0, 1, 2])

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=120,
        )

        # Should proceed without error (or complete)
        assert result.returncode == 0
        # Check that state was updated
        state_file = output_dir / ".state.json"
        assert state_file.exists()

        with open(state_file) as f:
            state = json.load(f)

        # Should have progressed past phase 3 or completed
        assert state["current_phase"] > 3 or state["status"] == "completed"

    def test_resume_workflow__should_skip_completed__when_phases_done(self, tmp_path, gmkit_cli, src_path):
        """Resume doesn't re-run phases that were already completed."""
        output_dir = tmp_path / "output"

        # Create state with phases 0-4 completed
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0, 1, 2, 3, 4])

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=120,
        )

        assert result.returncode == 0
        # Check state file
        with open(output_dir / ".state.json") as f:
            state = json.load(f)

        # completed_phases should still include the original ones
        for phase in [0, 1, 2, 3, 4]:
            assert phase in state["completed_phases"]


class TestResumeErrorCases:
    """Tests for resume error handling."""

    def test_resume_workflow__should_fail__when_no_state_file(self, tmp_path, gmkit_cli, src_path):
        """--resume fails gracefully when no state file exists."""
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=30,
        )

        assert result.returncode != 0
        expected = format_error(ErrorMessages.STATE_MISSING, str(tmp_path.resolve()))
        # Expect: "ERROR: Cannot resume - state file missing or corrupt (<dir>)\n  Use 'gmkit pdf-convert <pdf-path>' to start fresh"
        assert expected in result.stderr

    def test_resume_workflow__should_fail__when_state_corrupt(self, tmp_path, gmkit_cli, src_path):
        """--resume fails gracefully with corrupt state file."""
        (tmp_path / ".state.json").write_text("not valid json{")

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=30,
        )

        assert result.returncode != 0
        error_context = ""
        try:
            json.loads("not valid json{")
        except json.JSONDecodeError as exc:
            error_context = str(exc)

        expected = format_error(
            ErrorMessages.STATE_CORRUPT,
            f"State file is not valid JSON: {error_context}",
        )
        # Expect: "ERROR: State file is corrupted (State file is not valid JSON: <json error>)\n  Delete .state.json and restart conversion"
        assert expected in result.stderr

    def test_resume_workflow__should_fail__when_pdf_missing(self, tmp_path, gmkit_cli, src_path):
        """--resume fails when source PDF no longer exists."""
        output_dir = tmp_path / "output"
        fake_pdf = tmp_path / "deleted.pdf"

        # Create state pointing to non-existent PDF
        create_partial_state(output_dir, fake_pdf, completed_phases=[0, 1])

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(output_dir),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=30,
        )

        assert result.returncode != 0
        expected = f"ERROR: Source PDF not found: {fake_pdf.resolve()}"
        # Expect: "ERROR: Source PDF not found: <pdf path>"
        assert expected in result.stderr


class TestPhaseRerun:
    """Tests for re-running specific phases."""

    def test_phase_rerun__should_run_single_phase__when_valid_phase(self, tmp_path, gmkit_cli, src_path):
        """--phase N re-runs only phase N."""
        output_dir = tmp_path / "output"

        # Create state with all phases completed
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0, 1, 2, 3, 4, 5])

        # Mark status as completed
        with open(output_dir / ".state.json") as f:
            state = json.load(f)
        state["status"] = "completed"
        state["current_phase"] = 5
        with open(output_dir / ".state.json", "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(output_dir),
                "--phase", "3",
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=60,
        )

        # Should succeed (mock phases always succeed)
        assert result.returncode == 0

    def test_phase_rerun__should_fail__when_prerequisites_missing(self, tmp_path, gmkit_cli, src_path):
        """--phase N fails if prerequisite phases aren't completed."""
        output_dir = tmp_path / "output"

        # Create state with only phase 0 completed
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0])

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(output_dir),
                "--phase", "5",
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=30,
        )

        assert result.returncode != 0
        output = (result.stdout + result.stderr).lower()
        assert "phase" in output and ("require" in output or "complete" in output)

    def test_phase_rerun__should_update_state__when_phase_completes(self, tmp_path, gmkit_cli, src_path):
        """--phase N updates state after re-running (T046)."""
        output_dir = tmp_path / "output"

        # Create state with phases 0-5 completed
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0, 1, 2, 3, 4, 5])

        # Mark status as completed
        with open(output_dir / ".state.json") as f:
            state = json.load(f)
        state["status"] = "completed"
        state["current_phase"] = 5
        original_updated_at = state["updated_at"]
        with open(output_dir / ".state.json", "w") as f:
            json.dump(state, f)

        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(output_dir),
                "--phase", "3",
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=60,
        )

        assert result.returncode == 0

        # Verify state was updated
        with open(output_dir / ".state.json") as f:
            new_state = json.load(f)

        # updated_at should have changed
        assert new_state["updated_at"] != original_updated_at
        # Phase 3 should still be in completed_phases (or may have been re-added)
        assert 3 in new_state["completed_phases"]


class TestFromStepResume:
    """Tests for resuming from specific step."""

    def test_from_step__should_reject__when_invalid_format(self, tmp_path, gmkit_cli, src_path):
        """--from-step validates step format."""
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(tmp_path),
                "--from-step", "invalid",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=30,
        )

        assert result.returncode != 0
        output = (result.stdout + result.stderr).lower()
        assert "invalid" in output or "format" in output

    def test_from_step__should_start_at_step__when_valid_format(self, tmp_path, gmkit_cli, src_path):
        """--from-step N.N starts from the specified step."""
        output_dir = tmp_path / "output"

        # Create state with phases 0-4 completed
        create_partial_state(output_dir, TEST_PDF_PATH, completed_phases=[0, 1, 2, 3, 4])

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(output_dir),
                "--from-step", "5.2",
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": src_path},
            timeout=120,
        )

        assert result.returncode == 0
        # Check state was updated
        with open(output_dir / ".state.json") as f:
            state = json.load(f)

        # Should have started from step 5.2
        # (the config should record from_step)
        assert state.get("config", {}).get("from_step") == "5.2" or state["status"] == "completed"
