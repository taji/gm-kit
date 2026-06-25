from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.cli_helpers import (
    run_analyze_and_prep_command,
    run_revise_prep_guidance_command,
)


def test_run_analyze_and_prep_command__should_require_pdf_path__when_new_run_requested(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as excinfo:
        run_analyze_and_prep_command(
            pdf_path=None,
            output=None,
            resume=False,
            status=False,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: PDF path is required for new prep\n"


def test_run_analyze_and_prep_command__should_route_to_new_prep__when_pdf_path_provided(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"
    workspace_path = tmp_path / "workspace"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    with patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls:
        mock_cls.return_value.run_new_prep.return_value = ExitCode.SUCCESS

        with pytest.raises(typer.Exit) as excinfo:
            run_analyze_and_prep_command(
                pdf_path=str(pdf_path),
                output=str(workspace_path),
                resume=False,
                status=False,
                yes=True,
            )

    assert excinfo.value.exit_code == ExitCode.SUCCESS
    mock_cls.return_value.run_new_prep.assert_called_once_with(
        pdf_path,
        output_dir=workspace_path,
        auto_proceed=True,
    )


def test_run_analyze_and_prep_command__should_reject_combined_status_and_resume_flags__when_both_requested(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as excinfo:
        run_analyze_and_prep_command(
            pdf_path="workspace",
            output=None,
            resume=True,
            status=True,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: Cannot combine --resume and --status\n"


def test_run_analyze_and_prep_command__should_route_to_show_status__when_status_requested(
    tmp_path: Path,
) -> None:
    workspace_path = tmp_path / "workspace"

    with patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls:
        mock_cls.return_value.show_status.return_value = ExitCode.STATE_ERROR

        with pytest.raises(typer.Exit) as excinfo:
            run_analyze_and_prep_command(
                pdf_path=None,
                output=str(workspace_path),
                resume=False,
                status=True,
                yes=False,
            )

    assert excinfo.value.exit_code == ExitCode.STATE_ERROR
    mock_cls.return_value.show_status.assert_called_once_with(workspace_path)


def test_run_analyze_and_prep_command__should_route_to_resume_prep__when_resume_requested(
    tmp_path: Path,
) -> None:
    workspace_path = tmp_path / "workspace"

    with patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls:
        mock_cls.return_value.resume_prep.return_value = ExitCode.FILE_ERROR

        with pytest.raises(typer.Exit) as excinfo:
            run_analyze_and_prep_command(
                pdf_path=None,
                output=str(workspace_path),
                resume=True,
                status=False,
                yes=True,
            )

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    mock_cls.return_value.resume_prep.assert_called_once_with(
        workspace_path,
        auto_proceed=True,
    )


def test_run_analyze_and_prep_command__should_require_target_path__when_status_requested_without_output_or_pdf_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as excinfo:
        run_analyze_and_prep_command(
            pdf_path=None,
            output=None,
            resume=False,
            status=True,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: Prep workspace path is required for status or resume\n"


def test_run_analyze_and_prep_command__should_require_target_path__when_resume_requested_without_output_or_pdf_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as excinfo:
        run_analyze_and_prep_command(
            pdf_path=None,
            output=None,
            resume=True,
            status=False,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: Prep workspace path is required for status or resume\n"


def test_run_analyze_and_prep_command__should_reject_ambiguous_target__when_status_requested_with_pdf_path_and_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls,
        pytest.raises(typer.Exit) as excinfo,
    ):
        run_analyze_and_prep_command(
            pdf_path="input.pdf",
            output="workspace",
            resume=False,
            status=True,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: Provide either pdf_path or --output for status or resume, not both\n"
    mock_cls.assert_not_called()


def test_run_analyze_and_prep_command__should_reject_ambiguous_target__when_resume_requested_with_pdf_path_and_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with (
        patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls,
        pytest.raises(typer.Exit) as excinfo,
    ):
        run_analyze_and_prep_command(
            pdf_path="input.pdf",
            output="workspace",
            resume=True,
            status=False,
            yes=False,
        )

    captured = capsys.readouterr()

    assert excinfo.value.exit_code == ExitCode.FILE_ERROR
    assert captured.err == "ERROR: Provide either pdf_path or --output for status or resume, not both\n"
    mock_cls.assert_not_called()


def test_run_revise_prep_guidance_command__should_route_to_revision__when_workspace_provided(
    tmp_path: Path,
) -> None:
    workspace_path = tmp_path / "workspace"

    with patch("gm_kit.pdf_convert.prep.cli_helpers.PrepOrchestrator", autospec=True) as mock_cls:
        mock_cls.return_value.revise_prep_guidance.return_value = ExitCode.SUCCESS

        with pytest.raises(typer.Exit) as excinfo:
            run_revise_prep_guidance_command(str(workspace_path))

    assert excinfo.value.exit_code == ExitCode.SUCCESS
    mock_cls.return_value.revise_prep_guidance.assert_called_once_with(workspace_path)
