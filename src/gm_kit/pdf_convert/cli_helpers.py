from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from gm_kit.pdf_convert.active_conversion import (
    load_active_state,
    resolve_active_candidates,
    update_active_conversion,
)
from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN
from gm_kit.pdf_convert.errors import ErrorMessages, ExitCode, format_error

if TYPE_CHECKING:
    from gm_kit.pdf_convert.orchestrator import Orchestrator


def _resolve_active_dir(yes: bool) -> Path:
    """Resolve the active conversion directory from state or candidates.

    Args:
        yes: Whether to auto-select if only one candidate exists

    Returns:
        Path to the active conversion directory

    Raises:
        typer.Exit: If no active conversion found
    """
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


def _resolve_dir_or_active(pdf_path: str | None, output: str | None, yes: bool) -> Path:
    """Resolve directory from explicit path or active conversion.

    Args:
        pdf_path: Explicit PDF path if provided
        output: Explicit output directory if provided
        yes: Whether to auto-select active conversion

    Returns:
        Path to the target directory
    """
    if pdf_path or output:
        resolved = output or pdf_path
        if resolved is None:
            raise ValueError("Expected output or pdf_path to be provided")
        return Path(resolved)
    return _resolve_active_dir(yes)


def _update_active_if_exists(path: Path) -> None:
    """Update active conversion tracking if path exists.

    Args:
        path: Path to track as active conversion
    """
    if path.exists():
        update_active_conversion(Path.cwd(), path)


def _handle_status_command(
    pdf_path: str | None,
    output: str | None,
    yes: bool,
    orchestrator: Orchestrator,
) -> int:
    """Handle the --status command.

    Args:
        pdf_path: Explicit PDF path if provided
        output: Explicit output directory if provided
        yes: Whether to auto-select
        orchestrator: The orchestrator instance

    Returns:
        Exit code from the operation
    """
    status_path = _resolve_dir_or_active(pdf_path, output, yes)
    _update_active_if_exists(status_path)
    return orchestrator.show_status(status_path)


def _handle_resume_command(
    pdf_path: str | None,
    output: str | None,
    yes: bool,
    orchestrator: Orchestrator,
) -> int:
    """Handle the --resume command.

    Args:
        pdf_path: Explicit PDF path if provided
        output: Explicit output directory if provided
        yes: Whether to auto-select
        orchestrator: The orchestrator instance

    Returns:
        Exit code from the operation
    """
    resume_path = _resolve_dir_or_active(pdf_path, output, yes)
    _update_active_if_exists(resume_path)
    return orchestrator.resume_conversion(
        resume_path,
        auto_proceed=yes,
    )


def _handle_phase_command(
    pdf_path: str | None,
    output: str | None,
    phase: int,
    yes: bool,
    orchestrator: Orchestrator,
) -> int:
    """Handle the --phase command.

    Args:
        pdf_path: Explicit PDF path if provided
        output: Explicit output directory if provided
        phase: Phase number to run
        yes: Whether to auto-select
        orchestrator: The orchestrator instance

    Returns:
        Exit code from the operation

    Raises:
        typer.Exit: If phase number is invalid
    """
    if not PHASE_MIN <= phase <= PHASE_MAX:
        typer.echo(format_error(ErrorMessages.INVALID_PHASE, str(phase)), err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    dir_path = _resolve_dir_or_active(pdf_path, output, yes)
    _update_active_if_exists(dir_path)
    return orchestrator.run_single_phase(
        dir_path,
        phase,
        auto_proceed=yes,
    )


def _handle_from_step_command(
    pdf_path: str | None,
    output: str | None,
    from_step: str,
    yes: bool,
    orchestrator: Orchestrator,
) -> int:
    """Handle the --from-step command.

    Args:
        pdf_path: Explicit PDF path if provided
        output: Explicit output directory if provided
        from_step: Step identifier (e.g., "3.1")
        yes: Whether to auto-select
        orchestrator: The orchestrator instance

    Returns:
        Exit code from the operation

    Raises:
        typer.Exit: If step format is invalid
    """
    if not re.match(r"^\d+\.\d+$", from_step):
        typer.echo(format_error(ErrorMessages.INVALID_STEP, from_step), err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    dir_path = _resolve_dir_or_active(pdf_path, output, yes)
    _update_active_if_exists(dir_path)
    return orchestrator.run_from_step(
        dir_path,
        from_step,
        auto_proceed=yes,
    )


def _handle_new_conversion(  # noqa: PLR0913
    pdf_path: str,
    output: str | None,
    diagnostics: bool,
    yes: bool,
    gm_keyword: list[str] | None,
    gm_callout_config_file: str | None,
    orchestrator: Orchestrator,
    cli_args: str,
) -> int:
    """Handle new conversion command.

    Args:
        pdf_path: Path to the PDF file
        output: Optional output directory
        diagnostics: Whether to include diagnostics
        yes: Whether to auto-proceed
        gm_keyword: Custom GM keywords
        gm_callout_config_file: Path to callout config file
        orchestrator: The orchestrator instance
        cli_args: CLI arguments string for diagnostics

    Returns:
        Exit code from the operation
    """
    return orchestrator.run_new_conversion(
        Path(pdf_path),
        output_dir=Path(output) if output else None,
        diagnostics=diagnostics,
        auto_proceed=yes,
        cli_args=cli_args,
        gm_keyword=gm_keyword,
        gm_callout_config_file=gm_callout_config_file,
    )


def _validate_exclusive_flags(
    resume: bool,
    phase: int | None,
    from_step: str | None,
    status: bool,
) -> None:
    """Validate that only one operation flag is specified.

    Args:
        resume: Whether --resume flag is set
        phase: Phase number if --phase specified
        from_step: Step string if --from-step specified
        status: Whether --status flag is set

    Raises:
        typer.Exit: If multiple flags are specified
    """
    operation_flags = [resume, phase is not None, from_step, status]
    if sum(bool(f) for f in operation_flags) > 1:
        typer.echo(format_error(ErrorMessages.EXCLUSIVE_FLAGS), err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)


def run_pdf_convert_command(  # noqa: PLR0913
    pdf_path: str | None,
    output: str | None,
    resume: bool,
    phase: int | None,
    from_step: str | None,
    status: bool,
    diagnostics: bool,
    yes: bool,
    gm_keyword: list[str] | None,
    gm_callout_config_file: str | None,
) -> None:
    """Handle CLI routing for pdf-convert operations.

    Routes to appropriate handler based on command flags:
    - --status: Show conversion status
    - --resume: Resume conversion
    - --phase: Run specific phase
    - --from-step: Run from specific step
    - (none): New conversion
    """
    # Build CLI args string for diagnostics
    cli_args = " ".join(sys.argv[1:])

    # Check for mutually exclusive flags
    _validate_exclusive_flags(resume, phase, from_step, status)

    from gm_kit.pdf_convert.orchestrator import Orchestrator

    orchestrator = Orchestrator()

    # Route to appropriate handler
    if status:
        exit_code = _handle_status_command(pdf_path, output, yes, orchestrator)
        raise typer.Exit(code=exit_code)

    if resume:
        exit_code = _handle_resume_command(pdf_path, output, yes, orchestrator)
        raise typer.Exit(code=exit_code)

    if phase is not None:
        exit_code = _handle_phase_command(pdf_path, output, phase, yes, orchestrator)
        raise typer.Exit(code=exit_code)

    if from_step:
        exit_code = _handle_from_step_command(pdf_path, output, from_step, yes, orchestrator)
        raise typer.Exit(code=exit_code)

    # New conversion - pdf_path is required
    if not pdf_path:
        typer.echo("ERROR: PDF path is required for new conversion", err=True)
        typer.echo("Usage: gmkit pdf-convert <pdf-path> [OPTIONS]", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    exit_code = _handle_new_conversion(
        pdf_path,
        output,
        diagnostics,
        yes,
        gm_keyword,
        gm_callout_config_file,
        orchestrator,
        cli_args,
    )
    raise typer.Exit(code=exit_code)
