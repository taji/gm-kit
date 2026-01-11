from __future__ import annotations  # For type checking/hinting.

import sys
import typer  # CLI framework.

from gm_kit.agent_config import get_agent_config, list_supported_agents
from gm_kit.init import run_init
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
        typer.echo(f"- {workspace / agent_config.prompt_location}")
        typer.echo(f"GM-Kit initialized at: {workspace}")
    except ValidationError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
