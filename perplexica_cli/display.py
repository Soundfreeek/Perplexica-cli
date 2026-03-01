"""Terminal display and rendering for Perplexica CLI."""

import sys
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
err_console = Console(stderr=True)


def print_error(msg: str) -> None:
    err_console.print(f"[bold red]Error:[/bold red] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")


def print_answer(message: str) -> None:
    """Render a complete answer as a markdown panel."""
    md = Markdown(message)
    panel = Panel(md, title="[bold cyan]Answer[/bold cyan]", border_style="cyan", padding=(1, 2))
    console.print(panel)


def print_sources(sources: list[dict[str, Any]]) -> None:
    """Render sources as a numbered list."""
    if not sources:
        return
    console.print()
    table = Table(title="Sources", show_lines=False, border_style="dim")
    table.add_column("#", style="bold", width=4)
    table.add_column("Title", style="white", ratio=2)
    table.add_column("URL", style="blue underline", ratio=3)
    for i, src in enumerate(sources, 1):
        meta = src.get("metadata", {})
        title = meta.get("title", "Untitled")
        url = meta.get("url", "")
        table.add_row(str(i), title, url)
    console.print(table)


def stream_answer(events) -> tuple[str, list[dict[str, Any]]]:
    """Stream answer tokens to the terminal in real time.

    Returns the full message and sources when done.
    """
    full_message = ""
    sources: list[dict[str, Any]] = []

    console.print(Panel.fit("[bold cyan]Answer[/bold cyan]", border_style="cyan"))

    for event in events:
        event_type = event.get("type", "")
        data = event.get("data")

        if event_type == "sources" and isinstance(data, list):
            sources = data
        elif event_type == "response" and isinstance(data, str):
            full_message += data
            sys.stdout.write(data)
            sys.stdout.flush()
        elif event_type == "done":
            break

    sys.stdout.write("\n")
    sys.stdout.flush()
    return full_message, sources


def print_providers(providers: list[dict[str, Any]]) -> None:
    """Display available providers and their models."""
    if not providers:
        print_error("No providers configured. Open http://localhost:3000 to set up providers.")
        return

    for provider in providers:
        name = provider.get("name", "Unknown")
        pid = provider.get("id", "")
        console.print(f"\n[bold green]{name}[/bold green]  [dim]({pid})[/dim]")

        chat_models = provider.get("chatModels", [])
        if chat_models:
            console.print("  [bold]Chat Models:[/bold]")
            for m in chat_models:
                console.print(f"    - [cyan]{m['key']}[/cyan]  [dim]{m.get('name', '')}[/dim]")

        embed_models = provider.get("embeddingModels", [])
        if embed_models:
            console.print("  [bold]Embedding Models:[/bold]")
            for m in embed_models:
                console.print(f"    - [cyan]{m['key']}[/cyan]  [dim]{m.get('name', '')}[/dim]")


def prompt_select(label: str, options: list[dict[str, str]], key_field: str = "key") -> dict[str, str] | None:
    """Prompt the user to select from a list of options."""
    if not options:
        print_error(f"No options available for {label}.")
        return None

    console.print(f"\n[bold]{label}:[/bold]")
    for i, opt in enumerate(options, 1):
        display = opt.get("name", opt.get(key_field, "?"))
        console.print(f"  [bold]{i}.[/bold] {display} [dim]({opt.get(key_field, '')})[/dim]")

    while True:
        try:
            choice = console.input(f"\nSelect [1-{len(options)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, EOFError):
            pass
        console.print("[red]Invalid choice, try again.[/red]")
