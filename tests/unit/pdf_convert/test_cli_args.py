"""Unit tests for CLI argument parsing (T029).

Uses typer.testing.CliRunner to test argument parsing and routing
in-process without spawning subprocesses.
"""

import re
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gm_kit.cli import app
from gm_kit.pdf_convert.errors import ExitCode, ErrorMessages, format_error


runner = CliRunner()
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[mK]")


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


class TestFlagCombinations:
    """Tests for flag combinations."""

    def test_pdf_convert_cli__should_return_success__when_output_flag_provided(self, tmp_path):
        """Can specify both pdf_path and --output."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_new_conversion.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            # CliRunner.invoke() returns a Result whose .output captures
            # stdout+stderr and .exit_code captures the process exit code.
            # See: https://typer.tiangolo.com/tutorial/testing/#test-the-app
            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path / "test.pdf"),
                "--output", str(tmp_path / "output"),
            ])
        assert result.exit_code == 0

    def test_pdf_convert_cli__should_return_success__when_yes_flag_provided(self, tmp_path):
        """Can specify pdf_path and --yes."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_new_conversion.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path / "test.pdf"),
                "--yes",
            ])
        assert result.exit_code == 0

    def test_pdf_convert_cli__should_return_success__when_diagnostics_flag_provided(self, tmp_path):
        """Can specify pdf_path and --diagnostics."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_new_conversion.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path / "test.pdf"),
                "--diagnostics",
            ])
        assert result.exit_code == 0

    def test_pdf_convert_cli__should_return_success__when_compatible_flags_combined(self, tmp_path):
        """Can use --output, --yes, and --diagnostics together."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_new_conversion.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path / "test.pdf"),
                "--output", str(tmp_path / "output"),
                "--yes",
                "--diagnostics",
            ])
        assert result.exit_code == 0


class TestMutuallyExclusiveFlags:
    """Tests for mutually exclusive flag combinations."""

    def test_pdf_convert_cli__should_reject__when_resume_and_phase_combined(self, tmp_path):
        """--resume and --phase cannot be used together."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--resume", str(tmp_path),
            "--phase", "5",
        ])
        expected = format_error(ErrorMessages.EXCLUSIVE_FLAGS)
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_pdf_convert_cli__should_reject__when_resume_and_from_step_combined(self, tmp_path):
        """--resume and --from-step cannot be used together."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--resume", str(tmp_path),
            "--from-step", "5.3",
        ])
        expected = format_error(ErrorMessages.EXCLUSIVE_FLAGS)
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_pdf_convert_cli__should_reject__when_resume_and_status_combined(self, tmp_path):
        """--resume and --status cannot be used together."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--resume", str(tmp_path),
            "--status", str(tmp_path),
        ])
        expected = format_error(ErrorMessages.EXCLUSIVE_FLAGS)
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_pdf_convert_cli__should_reject__when_phase_and_from_step_combined(self, tmp_path):
        """--phase and --from-step cannot be used together."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--phase", "5",
            "--from-step", "5.3",
        ])
        expected = format_error(ErrorMessages.EXCLUSIVE_FLAGS)
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_pdf_convert_cli__should_reject__when_phase_and_status_combined(self, tmp_path):
        """--phase and --status cannot be used together."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--phase", "5",
            "--status", str(tmp_path),
        ])
        expected = format_error(ErrorMessages.EXCLUSIVE_FLAGS)
        # Expect: "ERROR: Cannot combine --resume, --phase, --from-step, or --status\n  Use only one operation mode"
        assert result.exit_code != 0
        assert expected in (result.output or "")


class TestValidPhaseValues:
    """Tests for valid --phase values (T044)."""

    def test_phase_flag__should_return_success__when_zero(self, tmp_path):
        """--phase accepts 0 (pre-flight phase)."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_single_phase.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path),
                "--phase", "0",
                "--yes",
            ])
        assert result.exit_code == 0

    def test_phase_flag__should_return_success__when_ten(self, tmp_path):
        """--phase accepts 10 (max phase)."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_single_phase.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path),
                "--phase", "10",
                "--yes",
            ])
        assert result.exit_code == 0

    def test_phase_flag__should_return_success__when_five(self, tmp_path):
        """--phase accepts middle values like 5."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_single_phase.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path),
                "--phase", "5",
                "--yes",
            ])
        assert result.exit_code == 0


class TestInvalidPhaseValues:
    """Tests for invalid --phase values."""

    def test_phase_flag__should_reject__when_negative(self, tmp_path):
        """--phase rejects negative numbers."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--phase", "-1",
        ])
        expected = format_error(ErrorMessages.INVALID_PHASE, "-1")
        # Expect: "ERROR: --phase requires an integer between 0 and 10 (-1)"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_phase_flag__should_reject__when_above_ten(self, tmp_path):
        """--phase rejects values > 10."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--phase", "11",
        ])
        expected = format_error(ErrorMessages.INVALID_PHASE, "11")
        # Expect: "ERROR: --phase requires an integer between 0 and 10 (11)"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_phase_flag__should_reject__when_non_integer(self, tmp_path):
        """--phase rejects non-integer values."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--phase", "abc",
        ])
        expected = "Invalid value for '--phase': 'abc' is not a valid integer."
        # Expect: "Invalid value for '--phase': 'abc' is not a valid integer."
        assert result.exit_code != 0
        clean_output = _strip_ansi(result.output or "")
        assert expected in clean_output


class TestValidFromStepValues:
    """Tests for valid --from-step values (T045)."""

    def test_from_step_flag__should_return_success__when_valid_format(self, tmp_path):
        """--from-step accepts valid N.N format."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_from_step.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path),
                "--from-step", "5.1",
                "--yes",
            ])
        assert result.exit_code == 0

    def test_from_step_flag__should_return_success__when_phase_zero_step(self, tmp_path):
        """--from-step accepts 0.1 format."""
        with patch("gm_kit.pdf_convert.orchestrator.Orchestrator") as mock_orch_cls:
            mock_orch = MagicMock()
            mock_orch.run_from_step.return_value = ExitCode.SUCCESS
            mock_orch_cls.return_value = mock_orch

            result = runner.invoke(app, [
                "pdf-convert",
                str(tmp_path),
                "--from-step", "0.1",
                "--yes",
            ])
        assert result.exit_code == 0


class TestInvalidFromStepValues:
    """Tests for invalid --from-step values."""

    def test_from_step_flag__should_reject__when_single_number(self, tmp_path):
        """--from-step rejects single number format."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--from-step", "5",
        ])
        expected = format_error(ErrorMessages.INVALID_STEP, "5")
        # Expect: "ERROR: --from-step requires format N.N (e.g., 5.3) (5)"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_from_step_flag__should_reject__when_triple_format(self, tmp_path):
        """--from-step rejects triple format like 5.3.1."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--from-step", "5.3.1",
        ])
        expected = format_error(ErrorMessages.INVALID_STEP, "5.3.1")
        # Expect: "ERROR: --from-step requires format N.N (e.g., 5.3) (5.3.1)"
        assert result.exit_code != 0
        assert expected in (result.output or "")

    def test_from_step_flag__should_reject__when_text_input(self, tmp_path):
        """--from-step rejects text input."""
        result = runner.invoke(app, [
            "pdf-convert",
            str(tmp_path),
            "--from-step", "abc",
        ])
        expected = format_error(ErrorMessages.INVALID_STEP, "abc")
        # Expect: "ERROR: --from-step requires format N.N (e.g., 5.3) (abc)"
        assert result.exit_code != 0
        assert expected in (result.output or "")


class TestPhaseRequiresDirectory:
    """Tests for --phase requiring directory path."""

    def test_phase_flag__should_fail__when_no_path_provided(self):
        """--phase without any path fails."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--phase", "5",
        ])
        expected = "ERROR: --phase requires a directory path"
        # Expect: "ERROR: --phase requires a directory path"
        assert result.exit_code != 0
        assert expected in (result.output or "")


class TestFromStepRequiresDirectory:
    """Tests for --from-step requiring directory path."""

    def test_from_step_flag__should_fail__when_no_path_provided(self):
        """--from-step without any path fails."""
        result = runner.invoke(app, [
            "pdf-convert",
            "--from-step", "5.3",
        ])
        expected = "ERROR: --from-step requires a directory path"
        # Expect: "ERROR: --from-step requires a directory path"
        assert result.exit_code != 0
        assert expected in (result.output or "")
