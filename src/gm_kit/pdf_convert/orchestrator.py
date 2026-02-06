"""Pipeline orchestration for PDF to Markdown conversion.

Coordinates phase execution, state management, and folder setup.
"""

from __future__ import annotations

import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gm_kit.pdf_convert.active_conversion import update_active_conversion
from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN, PHASE_NAMES
from gm_kit.pdf_convert.errors import ErrorMessages, ExitCode, format_error
from gm_kit.pdf_convert.metadata import PDFMetadata, extract_metadata, save_metadata
from gm_kit.pdf_convert.phases.base import Phase
from gm_kit.pdf_convert.phases.stubs import get_mock_phases
from gm_kit.pdf_convert.preflight import (
    analyze_pdf,
    display_preflight_report,
    prompt_user_confirmation,
)
from gm_kit.pdf_convert.state import (
    ConversionState,
    ConversionStatus,
    ErrorInfo,
    load_state,
    save_state,
    validate_state_for_resume,
)

logger = logging.getLogger(__name__)


# Characters that are invalid in Windows filenames
WINDOWS_INVALID_CHARS = '<>:"|?*'


def sanitize_filename(name: str) -> str:
    """Sanitize a filename for cross-platform compatibility.

    Replaces Windows-incompatible characters with underscores.

    Args:
        name: Original filename

    Returns:
        Sanitized filename
    """
    result = name
    for char in WINDOWS_INVALID_CHARS:
        result = result.replace(char, "_")
    return result


def create_output_directory(
    pdf_path: Path,
    output_dir: Path | None = None,
) -> Path:
    """Create the output directory structure per FR-021.

    Args:
        pdf_path: Path to source PDF
        output_dir: Optional output directory (defaults to ./<pdf-basename>/)

    Returns:
        Path to created output directory

    Raises:
        PermissionError: If directory cannot be created
    """
    if output_dir is None:
        # Default to ./<pdf-basename>/
        base_name = sanitize_filename(pdf_path.stem)
        output_dir = Path.cwd() / base_name
    else:
        output_dir = Path(output_dir).resolve()

    try:
        # Create main directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories per FR-021
        (output_dir / "images").mkdir(exist_ok=True)
        (output_dir / "preprocessed").mkdir(exist_ok=True)

        return output_dir

    except PermissionError as e:
        raise PermissionError(format_error(ErrorMessages.OUTPUT_DIR_ERROR, str(output_dir))) from e


def create_diagnostic_bundle(
    state: ConversionState,
    console: Console | None = None,
) -> Path | None:
    """Create diagnostic bundle at end of Phase 10 per FR-010b/c/d.

    Args:
        state: Current conversion state
        console: Console for output

    Returns:
        Path to bundle if created, None if failed
    """
    if not state.diagnostics_enabled:
        return None

    output_dir = Path(state.output_dir)
    bundle_path = output_dir / "diagnostic-bundle.zip"
    pdf_name = sanitize_filename(Path(state.pdf_path).stem)

    # Files to include per FR-010b
    files_to_include = [
        ".state.json",
        "metadata.json",
        "font-family-mapping.json",
        "toc-extracted.txt",
        "images/image-manifest.json",
        "conversion-report.md",
        f"{pdf_name}-phase4.md",
        f"{pdf_name}-phase5.md",
        f"{pdf_name}-phase6.md",
        f"{pdf_name}-phase8.md",
    ]

    try:
        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add files that exist
            for file_name in files_to_include:
                file_path = output_dir / file_name
                if file_path.exists():
                    zf.write(file_path, file_name)

            # Add CLI args
            cli_args = state.config.get("cli_args", "")
            zf.writestr("cli-args.txt", cli_args)

        return bundle_path

    except Exception as e:
        if console:
            Console(stderr=True, soft_wrap=True).print(format_error(ErrorMessages.BUNDLE_FAILED))
        logger.warning(f"Failed to create diagnostic bundle: {e}")
        return None


def generate_copyright_notice(metadata: PDFMetadata) -> str:
    """Generate copyright notice per FR-049/FR-050a.

    Args:
        metadata: PDF metadata

    Returns:
        Copyright notice as markdown comment
    """
    title = metadata.title or Path(metadata.copyright or "Unknown").name
    author = metadata.author or metadata.creator or "Unknown"
    copyright_text = metadata.copyright or "See original publication"
    source_file = title if title else "Unknown"
    converted_date = datetime.now().isoformat()[:10]

    return f"""<!--
COPYRIGHT NOTICE
================
This markdown file was converted from a copyrighted PDF for personal game
preparation use only. The text, structure, and content remain the intellectual
property of the original publisher. Do not redistribute, publish, or share
this file publicly. For official content, please purchase from the publisher.

Title: {title}
Author/Publisher: {author}
Copyright: {copyright_text}
Source file: {source_file}
Converted: {converted_date}
Tool: GM-Kit pdf-convert
-->

"""


def insert_copyright_notice(markdown_path: Path, notice: str) -> None:
    """Insert copyright notice at the beginning of a markdown file.

    Args:
        markdown_path: Path to markdown file
        notice: Copyright notice to insert
    """
    content = markdown_path.read_text(encoding="utf-8")
    markdown_path.write_text(notice + content, encoding="utf-8")


class Orchestrator:
    """Coordinates PDF conversion pipeline execution.

    Manages state, phase execution, and progress reporting.
    """

    def __init__(
        self,
        console: Console | None = None,
        phases: list[Phase] | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            console: Rich console for output
            phases: List of phases to use (defaults to mock phases)
        """
        self.console = console or Console()
        self.error_console = Console(stderr=True, soft_wrap=True)
        self.phases = phases or get_mock_phases()
        self._phase_map = {p.phase_num: p for p in self.phases}

    def run_new_conversion(  # noqa: PLR0911
        self,
        pdf_path: Path,
        output_dir: Path | None = None,
        diagnostics: bool = False,
        auto_proceed: bool = False,
        cli_args: str = "",
    ) -> ExitCode:
        """Start a new PDF conversion.

        Args:
            pdf_path: Path to source PDF
            output_dir: Optional output directory
            diagnostics: Enable diagnostic bundle
            auto_proceed: Skip user confirmation prompts
            cli_args: CLI arguments string for diagnostics

        Returns:
            Exit code
        """
        pdf_path = Path(pdf_path).resolve()

        # Validate PDF exists
        if not pdf_path.exists():
            self.error_console.print(format_error(ErrorMessages.PDF_NOT_FOUND, str(pdf_path)))
            return ExitCode.FILE_ERROR

        # Check if PDF is readable
        try:
            with open(pdf_path, "rb") as f:
                f.read(1)
        except PermissionError:
            self.error_console.print(format_error(ErrorMessages.PDF_PERMISSION, str(pdf_path)))
            return ExitCode.FILE_ERROR

        # Create output directory
        try:
            output_dir = create_output_directory(pdf_path, output_dir)
        except PermissionError as e:
            self.error_console.print(str(e))
            return ExitCode.FILE_ERROR

        update_active_conversion(output_dir, output_dir)

        # Check for existing state
        existing_state = load_state(output_dir)
        if existing_state is not None:
            return self._handle_existing_state(
                existing_state, pdf_path, output_dir, diagnostics, auto_proceed, cli_args
            )

        # Run pre-flight analysis (Phase 0)
        try:
            metadata = extract_metadata(pdf_path)
        except ValueError as e:
            if "encrypted" in str(e).lower():
                self.error_console.print(format_error(ErrorMessages.PDF_ENCRYPTED))
                return ExitCode.PDF_ERROR
            raise

        # Save metadata
        save_metadata(metadata, output_dir)

        # Analyze and display pre-flight report
        report = analyze_pdf(pdf_path)
        display_preflight_report(report, self.console)

        # Check for scanned PDF
        if not report.text_extractable:
            self.error_console.print(format_error(ErrorMessages.SCANNED_PDF))
            return ExitCode.PDF_ERROR

        # User confirmation
        if not prompt_user_confirmation(self.console, auto_proceed):
            self.console.print(format_error(ErrorMessages.USER_CANCELLED))
            return ExitCode.USER_ABORT

        # Create initial state
        state = ConversionState(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            diagnostics_enabled=diagnostics,
            config={"cli_args": cli_args, "auto_proceed": auto_proceed},
        )

        # Save initial state
        save_state(state)

        # Run remaining phases
        return self._run_phases(state, start_phase=1)

    def _handle_existing_state(  # noqa: PLR0913
        self,
        existing_state: ConversionState,
        pdf_path: Path,
        output_dir: Path,
        diagnostics: bool,
        auto_proceed: bool,
        cli_args: str,
    ) -> ExitCode:
        """Handle case where output directory has existing state.

        Args:
            existing_state: Existing state from directory
            pdf_path: Path to source PDF
            output_dir: Output directory path
            diagnostics: Enable diagnostic bundle
            auto_proceed: Skip user confirmation prompts
            cli_args: CLI arguments string

        Returns:
            Exit code
        """
        last_update = existing_state.updated_at[:19].replace(
            "T", " "
        )  # last_update is used to inform user of last update to .state.json
        self.console.print(
            f"WARNING: Existing conversion found in {output_dir}. Last activity: {last_update}."
        )
        self.console.print()
        self.console.print(
            "Options: [O]verwrite and start fresh, [R]esume from checkpoint, [A]bort?"
        )

        if auto_proceed:
            # Default to resume in auto mode
            choice = "R"
        else:
            while True:
                try:
                    choice = input("Your choice [O/R/A]: ").strip().upper()
                    if choice in ("O", "OVERWRITE"):
                        choice = "O"
                        break
                    elif choice in ("R", "RESUME"):
                        choice = "R"
                        break
                    elif choice in ("A", "ABORT"):
                        choice = "A"
                        break
                    else:
                        self.console.print("Please enter O, R, or A")
                except (EOFError, KeyboardInterrupt):
                    choice = "A"
                    break

        if choice == "A":
            self.console.print(format_error(ErrorMessages.USER_CANCELLED))
            return ExitCode.USER_ABORT

        if choice == "O":
            # Delete existing state and start fresh
            (output_dir / ".state.json").unlink(missing_ok=True)
            return self.run_new_conversion(
                pdf_path, output_dir, diagnostics, auto_proceed, cli_args
            )

        # Resume
        return self.resume_conversion(output_dir, auto_proceed)

    def resume_conversion(
        self,
        output_dir: Path,
        auto_proceed: bool = False,
    ) -> ExitCode:
        """Resume an interrupted conversion.

        Args:
            output_dir: Directory with existing state
            auto_proceed: Skip user confirmation prompts

        Returns:
            Exit code
        """
        output_dir = Path(output_dir).resolve()

        # Load state
        try:
            state = load_state(output_dir)
        except ValueError as e:
            self.error_console.print(format_error(ErrorMessages.STATE_CORRUPT, str(e)))
            return ExitCode.STATE_ERROR

        if state is None:
            self.error_console.print(format_error(ErrorMessages.STATE_MISSING, str(output_dir)))
            return ExitCode.STATE_ERROR

        # Validate state
        errors = validate_state_for_resume(state)
        if errors:
            for error in errors:
                self.error_console.print(f"ERROR: {error}")
            return ExitCode.STATE_ERROR

        # Check for stale in_progress
        if state.status == ConversionStatus.IN_PROGRESS:
            # Check if lock is stale (handled in load_state)
            self.console.print(
                "WARNING: Previous conversion appears to have been interrupted. "
                "Resuming from last completed step."
            )

        # Verify completed phase outputs exist
        for phase_num in state.completed_phases:
            # Check if phase output file exists (if applicable)
            pdf_name = sanitize_filename(Path(state.pdf_path).stem)
            if phase_num in (4, 5, 6, 8):
                expected_output = output_dir / f"{pdf_name}-phase{phase_num}.md"
                if not expected_output.exists():
                    self.error_console.print(
                        format_error(
                            ErrorMessages.OUTPUT_MISSING,
                            f"Phase {phase_num}: {expected_output.name}",
                        )
                    )
                    return ExitCode.STATE_ERROR

        # Update state config
        state.config["auto_proceed"] = auto_proceed
        state.status = ConversionStatus.IN_PROGRESS

        # Resume from next phase after last completed
        start_phase = max(state.completed_phases) + 1 if state.completed_phases else 0

        return self._run_phases(state, start_phase=start_phase)

    def run_single_phase(
        self,
        output_dir: Path,
        phase_num: int,
        auto_proceed: bool = False,
    ) -> ExitCode:
        """Re-run a single phase.

        Args:
            output_dir: Directory with existing state
            phase_num: Phase number to run
            auto_proceed: Skip user confirmation prompts

        Returns:
            Exit code
        """
        output_dir = Path(output_dir).resolve()

        # Validate phase number
        if not PHASE_MIN <= phase_num <= PHASE_MAX:
            self.error_console.print(format_error(ErrorMessages.INVALID_PHASE, str(phase_num)))
            return ExitCode.FILE_ERROR

        # Load state
        state = load_state(output_dir)
        if state is None:
            self.error_console.print(format_error(ErrorMessages.STATE_MISSING, str(output_dir)))
            return ExitCode.STATE_ERROR

        # Check prerequisites
        if phase_num > 0:
            required_phases = list(range(phase_num))
            missing = [p for p in required_phases if p not in state.completed_phases]
            if missing:
                self.error_console.print(
                    f"ERROR: Phase {phase_num} requires phases {missing} to be completed first"
                )
                return ExitCode.STATE_ERROR

        # Update state
        state.config["auto_proceed"] = auto_proceed
        state.set_current_phase(phase_num)

        # Run just this phase
        return self._run_single_phase(state, phase_num)

    def run_from_step(
        self,
        output_dir: Path,
        step_id: str,
        auto_proceed: bool = False,
    ) -> ExitCode:
        """Resume from a specific step.

        Args:
            output_dir: Directory with existing state
            step_id: Step identifier (N.N format)
            auto_proceed: Skip user confirmation prompts

        Returns:
            Exit code
        """
        output_dir = Path(output_dir).resolve()

        # Validate step format
        if not re.match(r"^\d+\.\d+$", step_id):
            self.error_console.print(format_error(ErrorMessages.INVALID_STEP, step_id))
            return ExitCode.FILE_ERROR

        phase_num = int(step_id.split(".")[0])

        # Validate phase number
        if not PHASE_MIN <= phase_num <= PHASE_MAX:
            self.error_console.print(format_error(ErrorMessages.INVALID_PHASE, str(phase_num)))
            return ExitCode.FILE_ERROR

        # Load state
        state = load_state(output_dir)
        if state is None:
            self.error_console.print(format_error(ErrorMessages.STATE_MISSING, str(output_dir)))
            return ExitCode.STATE_ERROR

        # Update state
        state.config["auto_proceed"] = auto_proceed
        state.config["from_step"] = step_id
        state.set_current_phase(phase_num, step_id)

        # Run from this phase onwards
        return self._run_phases(state, start_phase=phase_num)

    def show_status(self, output_dir: Path) -> ExitCode:
        """Display conversion status per FR-009a.

        Args:
            output_dir: Directory with state file

        Returns:
            Exit code
        """
        output_dir = Path(output_dir).resolve()

        state = load_state(output_dir)
        if state is None:
            self.console.print("No conversion in progress in this directory.")
            return ExitCode.SUCCESS

        # Display status table
        self.console.print(f"Conversion Status: {output_dir}")
        self.console.print("─" * 40)

        pdf_name = Path(state.pdf_path).name
        # Get file size if exists
        try:
            size_mb = Path(state.pdf_path).stat().st_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
        except FileNotFoundError:
            size_str = "file not found"

        self.console.print(f"Source: {pdf_name} ({size_str})")
        self.console.print(f"Status: {state.status.value}")
        self.console.print(f"Started: {state.started_at[:19].replace('T', ' ')}")
        self.console.print()

        # Phase table
        self.console.print(f"{'Phase':<6} {'Name':<24} {'Status':<12} {'Completed'}")
        self.console.print("─" * 60)

        for phase_num in range(PHASE_MIN, PHASE_MAX + 1):
            name = PHASE_NAMES.get(phase_num, f"Phase {phase_num}")[:24]

            if phase_num in state.completed_phases:
                status = "completed"
                # Find completion time from phase_results
                completed_time = ""
                for result in state.phase_results:
                    if result.get("phase_num") == phase_num:
                        completed_time = result.get("completed_at", "")[:19].replace("T", " ")
                        break
            elif phase_num == state.current_phase:
                status = f"in_progress (step {state.current_step})"
                completed_time = ""
            else:
                status = "pending"
                completed_time = ""

            self.console.print(f"{phase_num:<6} {name:<24} {status:<12} {completed_time}")

        # Error summary if failed
        if state.status == ConversionStatus.FAILED and state.error:
            self.console.print()
            self.console.print(f"[red]Error:[/red] {state.error.message}")
            if state.error.suggestion:
                self.console.print(f"Suggestion: {state.error.suggestion}")

        return ExitCode.SUCCESS

    def _run_phases(
        self,
        state: ConversionState,
        start_phase: int = 0,
    ) -> ExitCode:
        """Run phases from start_phase through 10.

        Args:
            state: Current conversion state
            start_phase: Phase to start from

        Returns:
            Exit code
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            for phase_num in range(start_phase, PHASE_MAX + 1):
                phase_name = PHASE_NAMES.get(phase_num, f"Phase {phase_num}")
                task = progress.add_task(
                    f"Phase {phase_num}/{PHASE_MAX}: {phase_name}...",
                    total=None,
                )

                exit_code = self._run_single_phase(state, phase_num)

                progress.remove_task(task)

                if exit_code != ExitCode.SUCCESS:
                    return exit_code

        # Create diagnostic bundle if enabled
        if state.diagnostics_enabled:
            create_diagnostic_bundle(state, self.console)

        # Mark as completed
        state.set_completed()
        save_state(state)

        self.console.print()
        self.console.print("[green]Conversion completed successfully![/green]")

        return ExitCode.SUCCESS

    def _run_single_phase(
        self,
        state: ConversionState,
        phase_num: int,
    ) -> ExitCode:
        """Run a single phase.

        Args:
            state: Current conversion state
            phase_num: Phase to run

        Returns:
            Exit code
        """
        phase = self._phase_map.get(phase_num)
        if phase is None:
            self.error_console.print(f"ERROR: Phase {phase_num} not found")
            return ExitCode.STATE_ERROR

        # Update state
        state.set_current_phase(phase_num)
        save_state(state)

        # Execute phase
        try:
            result = phase.execute(state)
        except Exception as e:
            logger.exception(f"Phase {phase_num} failed with exception")
            error = ErrorInfo(
                phase=phase_num,
                step=state.current_step,
                code="PHASE_EXCEPTION",
                message=str(e),
                recoverable=True,
                suggestion=f"Re-run phase with: gmkit pdf-convert --phase {phase_num}",
            )
            state.set_failed(error)
            save_state(state)
            self.error_console.print(f"ERROR: Phase {phase_num} failed: {e}")
            return ExitCode.PDF_ERROR

        # Handle result
        if result.is_error:
            error = ErrorInfo(
                phase=phase_num,
                step=state.current_step,
                code="PHASE_ERROR",
                message=result.errors[0] if result.errors else "Unknown error",
                recoverable=True,
                suggestion=f"Re-run phase with: gmkit pdf-convert --phase {phase_num}",
            )
            state.set_failed(error)
            save_state(state)

            for error_msg in result.errors:
                self.error_console.print(f"ERROR: {error_msg}")

            return ExitCode.PDF_ERROR

        # Log warnings
        for warning in result.warnings:
            self.console.print(f"[yellow]WARNING:[/yellow] {warning}")

        # Mark phase complete
        state.mark_phase_completed(phase_num, result.to_dict())
        save_state(state)

        return ExitCode.SUCCESS
