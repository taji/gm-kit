from __future__ import annotations  # For type checking/hinting.

import sys
import typer  # CLI framework.

from gm_kit.agent_config import get_agent_config, list_supported_agents
from gm_kit.init import run_init
from gm_kit.pdf_convert.constants import PHASE_MAX, PHASE_MIN
from gm_kit.validator import ValidationError

app = typer.Typer(help="GM-Kit CLI")


# Required to allow subcommands via typer, consider this a noop function called by typer to provide a command group (so init below).
@app.callback(invoke_without_command=False)
def cli_root() -> None:
    """Entry point for GM-Kit CLI."""
    # Callback enables subcommands like `gmkit init`.
    return None


def _prompt_text_choice(label: str, choices: list[str]) -> str:
    choice_list = ", ".join(choices)
    prompt = f"{label} ({choice_list})"
    while True:
        value = typer.prompt(prompt).strip().lower()
        if value in choices:
            return value
        typer.echo(f"Invalid choice: {value}. Choose from: {choice_list}")


def _prompt_menu_choice(label: str, choices: list[str]) -> str:
    try:
        import readchar
        from rich.console import Console
        from rich.live import Live
        from rich.panel import Panel
        from rich.table import Table
    except ModuleNotFoundError as exc:
        typer.echo("Menu prompts require readchar and rich. Use --text-input or install dependencies.")
        raise typer.Exit(code=1) from exc
    console = Console()
    selected_index = 0

    def render_panel() -> Panel:
        table = Table.grid(padding=(0, 1))
        for index, choice in enumerate(choices):
            if index == selected_index:
                table.add_row("[bold cyan]>[/bold cyan]", f"[bold]{choice}[/bold]")
            else:
                table.add_row(" ", choice)
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select[/dim]")
        return Panel(table, title=f"[bold]{label}[/bold]")

    with Live(render_panel(), console=console, transient=True, auto_refresh=False) as live:
        while True:
            key = readchar.readkey()
            if key in (readchar.key.UP, readchar.key.CTRL_P):
                selected_index = (selected_index - 1) % len(choices)
            elif key in (readchar.key.DOWN, readchar.key.CTRL_N):
                selected_index = (selected_index + 1) % len(choices)
            elif key in (readchar.key.ENTER,):
                return choices[selected_index]
            elif key in (readchar.key.CTRL_C, readchar.key.ESC):
                raise typer.Exit(code=1)
            live.update(render_panel(), refresh=True)


@app.command()
def init(
    temp_path: str = typer.Argument(..., help="Path to temp workspace"),
    agent: str = typer.Option(None, help="Agent name (claude, codex-cli, gemini, qwen)"),
    os: str = typer.Option(None, help="Target OS (macos/linux, windows)"),
    text_input: bool = typer.Option(
        False,
        "--text-input",
        help="Use text prompts instead of menu selection.",
    ),
) -> None:
    try:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            text_input = True
        if agent is None:
            if text_input:
                agent = _prompt_text_choice("Select agent", list(list_supported_agents()))
            else:
                agent = _prompt_menu_choice("Select agent", list(list_supported_agents()))
        if os is None:
            if text_input:
                os = _prompt_text_choice("Select OS", ["macos/linux", "windows"])
            else:
                os = _prompt_menu_choice("Select OS", ["macos/linux", "windows"])
        typer.echo("Initializing workspace...")
        workspace = run_init(temp_path=temp_path, agent=agent, os_type=os)
        agent_config = get_agent_config(agent)
        typer.echo("Created:")
        typer.echo(f"- {workspace / '.gmkit'}")
        prompt_dir = workspace / agent_config.prompt_location
        typer.echo(f"- {prompt_dir}")
        # List installed command files
        for cmd_file in sorted(prompt_dir.glob(f"gmkit.*{agent_config.file_extension}")):
            typer.echo(f"  - {cmd_file.name}")
        typer.echo(f"GM-Kit initialized at: {workspace}")
    except ValidationError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc


# PDF Convert command
@app.command("pdf-convert")
def pdf_convert(
    pdf_path: str = typer.Argument(
        None,
        help="Path to the PDF file to convert",
    ),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Output directory [default: ./<pdf-basename>/]",
    ),
    resume: str = typer.Option(
        None,
        "--resume", "-r",
        help="Resume interrupted conversion in directory",
    ),
    phase: int = typer.Option(
        None,
        "--phase",
        help=f"Re-run specific phase ({PHASE_MIN}-{PHASE_MAX})",
    ),
    from_step: str = typer.Option(
        None,
        "--from-step",
        help="Re-run from specific step (e.g., 5.3)",
    ),
    status: str = typer.Option(
        None,
        "--status", "-s",
        help="Show conversion status for directory",
    ),
    diagnostics: bool = typer.Option(
        False,
        "--diagnostics",
        help="Include diagnostic bundle in output",
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Non-interactive mode (accept defaults)",
    ),
) -> None:
    """Convert PDF to Markdown.

    gmkit pdf-convert - Convert PDF to Markdown (v0.1.0)

    Examples:
        gmkit pdf-convert my-module.pdf
        gmkit pdf-convert my-module.pdf --output ./converted/ --diagnostics
        gmkit pdf-convert --resume ./converted/
        gmkit pdf-convert --status ./converted/
    """
    from pathlib import Path
    from gm_kit.pdf_convert.orchestrator import Orchestrator
    from gm_kit.pdf_convert.errors import ExitCode, ErrorMessages, format_error

    # Build CLI args string for diagnostics
    cli_args = " ".join(sys.argv[1:])

    # Check for mutually exclusive flags
    operation_flags = [resume, phase is not None, from_step, status]
    if sum(bool(f) for f in operation_flags) > 1:
        typer.echo(format_error(ErrorMessages.EXCLUSIVE_FLAGS), err=True)
        raise typer.Exit(code=ExitCode.FILE_ERROR)

    orchestrator = Orchestrator()

    # Handle different operation modes
    if status:
        exit_code = orchestrator.show_status(Path(status))
        raise typer.Exit(code=exit_code)

    if resume:
        exit_code = orchestrator.resume_conversion(
            Path(resume),
            auto_proceed=yes,
        )
        raise typer.Exit(code=exit_code)

    if phase is not None:
        if not pdf_path and not output:
            typer.echo("ERROR: --phase requires a directory path", err=True)
            raise typer.Exit(code=ExitCode.FILE_ERROR)
        dir_path = Path(output or pdf_path)
        exit_code = orchestrator.run_single_phase(
            dir_path,
            phase,
            auto_proceed=yes,
        )
        raise typer.Exit(code=exit_code)

    if from_step:
        if not pdf_path and not output:
            typer.echo("ERROR: --from-step requires a directory path", err=True)
            raise typer.Exit(code=ExitCode.FILE_ERROR)
        dir_path = Path(output or pdf_path)
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
