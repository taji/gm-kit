from __future__ import annotations

import re
import sys
from pathlib import Path

import typer

from gm_kit.pdf_convert.active_conversion import (
    load_active_state,
    resolve_active_candidates,
    update_active_conversion,
)
from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN
from gm_kit.pdf_convert.errors import ErrorMessages, ExitCode, format_error


def run_pdf_convert_command(  # noqa: PLR0913, PLR0915
    pdf_path: str | None,
    output: str | None,
    resume: bool,
    phase: int | None,
    from_step: str | None,
    status: bool,
    diagnostics: bool,
    yes: bool,
) -> None:
    """Handle CLI routing for pdf-convert operations."""

    def _resolve_active_dir() -> Path:
        state = load_active_state(Path.cwd())
        if state:
            active = state.get("active", {})
            active_path = active.get("path")
            if active_path and Path(active_path).exists():
                return Path(active_path).resolve()

        candidates = resolve_active_candidates(Path.cwd())
        if not candidates:
            typer.echo(format_error(ErrorMessages.ACTIVE_CONVERSION_MISSING), err=True)
            raise typer.Exit(code=ExitCode.STATE_ERROR)

        if yes or len(candidates) == 1:
            return candidates[0]

        typer.echo("Multiple active conversions found:")
        for index, candidate in enumerate(candidates, start=1):
            typer.echo(f"{index}) {candidate}")

        while True:
            choice = typer.prompt("Select conversion", default="1")
            if choice.isdigit():
                selection = int(choice)
                if 1 <= selection <= len(candidates):
                    return candidates[selection - 1]
            typer.echo("Invalid selection. Enter a number from the list.")

    def _resolve_dir_or_active() -> Path:
        if pdf_path or output:
            resolved = output or pdf_path
            if resolved is None:
                raise ValueError("Expected output or pdf_path to be provided")
            return Path(resolved)
        return _resolve_active_dir()

    def _update_active_if_exists(path: Path) -> None:
        if path.exists():
            update_active_conversion(Path.cwd(), path)

    # Build CLI args string for diagnostics
    cli_args = " ".join(sys.argv[1:])

    # Check for mutually exclusive flags
    operation_flags = [resume, phase is not None, from_step, status]
    if sum(bool(f) for f in operation_flags) > 1:
        typer.echo(format_error(ErrorMessages.EXCLUSIVE_FLAGS), err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    from gm_kit.pdf_convert.orchestrator import Orchestrator

    orchestrator = Orchestrator()

    if status:
        status_path = _resolve_dir_or_active()
        _update_active_if_exists(status_path)
        exit_code = orchestrator.show_status(status_path)
        raise typer.Exit(code=exit_code)

    if resume:
        resume_path = _resolve_dir_or_active()
        _update_active_if_exists(resume_path)
        exit_code = orchestrator.resume_conversion(
            resume_path,
            auto_proceed=yes,
        )
        raise typer.Exit(code=exit_code)

    if phase is not None:
        if not PHASE_MIN <= phase <= PHASE_MAX:
            typer.echo(format_error(ErrorMessages.INVALID_PHASE, str(phase)), err=True)
            raise typer.Exit(code=ExitCode.FILE_ERROR)
        dir_path = _resolve_dir_or_active()
        _update_active_if_exists(dir_path)
        exit_code = orchestrator.run_single_phase(
            dir_path,
            phase,
            auto_proceed=yes,
        )
        raise typer.Exit(code=exit_code)

    if from_step:
        if not re.match(r"^\d+\.\d+$", from_step):
            typer.echo(format_error(ErrorMessages.INVALID_STEP, from_step), err=True)
            raise typer.Exit(code=ExitCode.FILE_ERROR)
        dir_path = _resolve_dir_or_active()
        _update_active_if_exists(dir_path)
        exit_code = orchestrator.run_from_step(
            dir_path,
            from_step,
            auto_proceed=yes,
        )
        raise typer.Exit(code=exit_code)

    # New conversion - pdf_path is required
    if not pdf_path:
        typer.echo("ERROR: PDF path is required for new conversion", err=True)
        typer.echo("Usage: gmkit pdf-convert <pdf-path> [OPTIONS]", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    exit_code = orchestrator.run_new_conversion(
        Path(pdf_path),
        output_dir=Path(output) if output else None,
        diagnostics=diagnostics,
        auto_proceed=yes,
        cli_args=cli_args,
    )
    raise typer.Exit(code=exit_code)
