"""Integration tests for PDF conversion CLI (T020, T031)."""

import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

# Test PDF path
TEST_PDF_PATH = Path(__file__).parent.parent.parent.parent / (
    "tests/fixtures/pdf_convert/The Homebrewery - NaturalCrit.pdf"
)
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mK]")


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


@pytest.fixture
def gmkit_cli():
    """Get path to gmkit CLI entry point."""
    # Run as module
    return [sys.executable, "-m", "gm_kit.cli"]


class TestNewConversion:
    """Tests for new conversion via CLI."""

    def test_full_pipeline__should_create_output_dir__when_valid_pdf(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert creates output directory."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",  # Skip confirmation
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=60,
        )

        # Should create output directory
        assert result.returncode == 0
        assert output_dir.exists()

    def test_full_pipeline__should_create_state_file__when_valid_pdf(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert creates .state.json."""
        output_dir = tmp_path / "output"

        subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=60,
        )

        state_file = output_dir / ".state.json"
        assert state_file.exists()
        with open(state_file) as f:
            data = json.load(f)
        assert "version" in data
        assert "pdf_path" in data
        assert "status" in data

    def test_full_pipeline__should_create_metadata_file__when_valid_pdf(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert creates metadata.json."""
        output_dir = tmp_path / "output"

        subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=60,
        )

        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()
        with open(metadata_file) as f:
            data = json.load(f)
        assert "page_count" in data
        assert data["page_count"] > 0

    def test_full_pipeline__should_use_pdf_basename__when_no_output_specified(self, tmp_path, gmkit_cli, monkeypatch):
        """gmkit pdf-convert defaults to ./<pdf-basename>/."""
        # Copy test PDF to tmp_path
        import shutil
        local_pdf = tmp_path / "test-document.pdf"
        shutil.copy(TEST_PDF_PATH, local_pdf)

        # Get absolute path to src directory
        src_path = Path(__file__).parent.parent.parent.parent / "src"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(local_pdf),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(src_path.resolve())},
            cwd=str(tmp_path),
            timeout=60,
        )

        # Should create directory named after PDF
        assert result.returncode == 0
        expected_dir = tmp_path / "test-document"
        assert expected_dir.exists()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_full_pipeline__should_return_error__when_pdf_missing(self, gmkit_cli, tmp_path):
        """gmkit pdf-convert with missing PDF returns error."""
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(tmp_path / "nonexistent.pdf"),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=30,
        )

        assert result.returncode != 0
        expected = (
            f"ERROR: Cannot open PDF - file not found or corrupted ({tmp_path / 'nonexistent.pdf'})\n"
            "  Check the file path and ensure the file exists"
        )
        # Expect: "ERROR: Cannot open PDF - file not found or corrupted (<path>)\n  Check the file path and ensure the file exists"
        assert expected in result.stderr

    def test_full_pipeline__should_reject__when_mutually_exclusive_flags(self, gmkit_cli, tmp_path):
        """gmkit pdf-convert rejects mutually exclusive flags."""
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--resume", str(tmp_path),
                "--phase", "5",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=30,
        )

        assert result.returncode != 0
        expected = (
            "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n"
            "  Use only one operation mode"
        )
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert expected in result.stderr

    def test_full_pipeline__should_show_usage__when_no_pdf_path(self, gmkit_cli):
        """gmkit pdf-convert without PDF path shows error."""
        result = subprocess.run(
            gmkit_cli + ["pdf-convert"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=30,
        )

        assert result.returncode != 0
        expected = (
            "ERROR: PDF path is required for new conversion\n"
            "Usage: gmkit pdf-convert <pdf-path> [OPTIONS]"
        )
        # Expect: "ERROR: PDF path is required for new conversion\nUsage: gmkit pdf-convert <pdf-path> [OPTIONS]"
        assert expected in result.stderr


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_full_pipeline__should_show_usage__when_help_flag(self, gmkit_cli):
        """gmkit pdf-convert --help shows usage."""
        result = subprocess.run(
            gmkit_cli + ["pdf-convert", "--help"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=30,
        )

        assert result.returncode == 0
        clean_stdout = _strip_ansi(result.stdout)
        assert "pdf-convert" in clean_stdout.lower()
        assert "Usage:" in clean_stdout
        assert "--output" in clean_stdout
        assert "--resume" in clean_stdout
        assert "--diagnostics" in clean_stdout


class TestStatusCommand:
    """Tests for --status flag."""

    def test_status_command__should_show_state__when_conversion_exists(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert --status shows conversion state."""
        # First create a state
        output_dir = tmp_path / "output"

        subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=60,
        )

        # Now check status
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--status", str(output_dir),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            cwd=str(tmp_path),
            timeout=30,
        )

        state_file = output_dir / ".state.json"
        assert state_file.exists()
        # Check for status information in output
        assert "phase" in result.stdout.lower() or "status" in result.stdout.lower()

    def test_status_command__should_show_message__when_no_state(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert --status with no state shows informative message."""
        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--status", str(tmp_path),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            cwd=str(tmp_path),
            timeout=30,
        )

        # Should show informative message about no conversion
        output = (result.stdout + result.stderr).lower()
        assert "no conversion" in output or "not found" in output or "no state" in output

    def test_status_command__should_show_partial_completion__when_at_phase_6(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert --status shows partial completion at Phase 6 (T052)."""
        from datetime import datetime

        # Create state at phase 6
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        state = {
            "version": "1.0",
            "pdf_path": str(tmp_path / "test.pdf"),
            "output_dir": str(output_dir),
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_phase": 6,
            "current_step": "6.2",
            "completed_phases": [0, 1, 2, 3, 4, 5],
            "phase_results": [],
            "status": "in_progress",
            "error": None,
            "diagnostics_enabled": False,
            "config": {},
        }
        (output_dir / ".state.json").write_text(json.dumps(state))

        # Create dummy PDF for status display
        (tmp_path / "test.pdf").write_bytes(b"%PDF-1.4 test")

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                "--status", str(output_dir),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            cwd=str(tmp_path),
            timeout=30,
        )

        assert result.returncode == 0
        output = result.stdout.lower()

        # Should show phases 0-5 as completed
        assert "completed" in output
        # Should show phase 6 as in_progress
        assert "in_progress" in output
        # Should show step 6.2
        assert "6.2" in result.stdout


class TestPreflightDisplay:
    """Tests for pre-flight report display (FR-016a)."""

    def test_preflight__should_display_report__when_valid_pdf(self, tmp_path, gmkit_cli):
        """Pre-flight report is displayed with key metrics."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=60,
        )

        output = result.stdout + result.stderr

        # Check for pre-flight report elements (FR-016a)
        assert any(term in output.lower() for term in ["pre-flight", "preflight", "analysis"])
        # Should show page count or images or complexity
        assert any(term in output.lower() for term in ["page", "image", "complexity", "text"])


class TestDiagnosticsFlag:
    """Tests for --diagnostics flag (T031)."""

    def test_diagnostics__should_create_bundle__when_flag_enabled(self, tmp_path, gmkit_cli):
        """gmkit pdf-convert --diagnostics creates diagnostic-bundle.zip."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
                "--diagnostics",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=120,  # Longer timeout for full conversion
        )

        # If conversion completes, bundle should exist
        bundle_path = output_dir / "diagnostic-bundle.zip"
        assert result.returncode == 0
        assert bundle_path.exists(), "Diagnostic bundle should be created on success"
        assert zipfile.is_zipfile(bundle_path), "Bundle should be valid zip file"

    def test_diagnostics__should_contain_state__when_bundle_created(self, tmp_path, gmkit_cli):
        """Diagnostic bundle contains .state.json per FR-010b."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
                "--diagnostics",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=120,
        )

        bundle_path = output_dir / "diagnostic-bundle.zip"
        assert result.returncode == 0
        assert bundle_path.exists()
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            assert ".state.json" in zf.namelist()

    def test_diagnostics__should_contain_metadata__when_bundle_created(self, tmp_path, gmkit_cli):
        """Diagnostic bundle contains metadata.json per FR-010b."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
                "--diagnostics",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=120,
        )

        bundle_path = output_dir / "diagnostic-bundle.zip"
        assert result.returncode == 0
        assert bundle_path.exists()
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            assert "metadata.json" in zf.namelist()

    def test_diagnostics__should_contain_cli_args__when_bundle_created(self, tmp_path, gmkit_cli):
        """Diagnostic bundle contains cli-args.txt per FR-010b."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
                "--diagnostics",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=120,
        )

        bundle_path = output_dir / "diagnostic-bundle.zip"
        assert result.returncode == 0
        assert bundle_path.exists()
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            assert "cli-args.txt" in zf.namelist()
            args_content = zf.read("cli-args.txt").decode()
            assert "--diagnostics" in args_content

    def test_diagnostics__should_skip_bundle__when_flag_not_set(self, tmp_path, gmkit_cli):
        """No diagnostic bundle created without --diagnostics flag."""
        output_dir = tmp_path / "output"

        subprocess.run(
            gmkit_cli + [
                "pdf-convert",
                str(TEST_PDF_PATH),
                "--output", str(output_dir),
                "--yes",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"},
            timeout=120,
        )

        bundle_path = output_dir / "diagnostic-bundle.zip"
        assert not bundle_path.exists(), "No bundle without --diagnostics"
