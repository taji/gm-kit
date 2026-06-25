from __future__ import annotations

from pathlib import Path

import typer

from gm_kit.pdf_convert.errors import ExitCode
from gm_kit.pdf_convert.prep.orchestrator import PrepOrchestrator


def _resolve_prep_target_path(pdf_path: str | None, output: str | None) -> Path:
    if pdf_path and output:
        typer.echo(
            "ERROR: Provide either pdf_path or --output for status or resume, not both",
            err=True,
        )
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    resolved = output or pdf_path
    if not resolved:
        typer.echo("ERROR: Prep workspace path is required for status or resume", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)
    return Path(resolved)


def run_analyze_and_prep_command(
    pdf_path: str | None,
    output: str | None,
    resume: bool,
    status: bool,
    yes: bool,
) -> None:
    operation_flags = [resume, status]
    if sum(bool(flag) for flag in operation_flags) > 1:
        typer.echo("ERROR: Cannot combine --resume and --status", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    if status:
        target_path = _resolve_prep_target_path(pdf_path, output)
        orchestrator = PrepOrchestrator()
        raise typer.Exit(code=orchestrator.show_status(target_path))

    if resume:
        target_path = _resolve_prep_target_path(pdf_path, output)
        orchestrator = PrepOrchestrator()
        raise typer.Exit(
            code=orchestrator.resume_prep(
                target_path,
                auto_proceed=yes,
            )
        )

    if not pdf_path:
        typer.echo("ERROR: PDF path is required for new prep", err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    orchestrator = PrepOrchestrator()
    raise typer.Exit(
        code=orchestrator.run_new_prep(
            Path(pdf_path),
            output_dir=Path(output) if output else None,
            auto_proceed=yes,
        )
    )


def run_revise_prep_guidance_command(workspace: str) -> None:
    """Finalize reviewed guidance from edited prep artifacts."""
    orchestrator = PrepOrchestrator()
    raise typer.Exit(code=orchestrator.revise_prep_guidance(Path(workspace)))
