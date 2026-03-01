"""CLI entry point for Perplexica CLI."""

import click
import httpx

from perplexica_cli.api import PerplexicaAPI
from perplexica_cli.config import load_config, save_config, is_configured
from perplexica_cli.display import (
    console,
    print_answer,
    print_error,
    print_info,
    print_providers,
    print_sources,
    prompt_select,
    stream_answer,
)


@click.group(invoke_without_command=True)
@click.option("--url", default=None, help="Override Perplexica server URL")
@click.pass_context
def cli(ctx: click.Context, url: str | None) -> None:
    """Perplexica CLI - AI-powered search from your terminal.

    \b
    Commands:
      perplexica search "What is Linux?"
      perplexica chat
      perplexica models
      perplexica setup
    """
    ctx.ensure_object(dict)
    config = load_config()

    if url:
        config["url"] = url

    ctx.obj["config"] = config

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="search")
@click.argument("query")
@click.option("--sources", "-s", default=None, help="Comma-separated sources: web,academic,discussions")
@click.option("--mode", "-m", type=click.Choice(["speed", "balanced", "quality"]), default=None,
              help="Optimization mode")
@click.option("--no-stream", is_flag=True, help="Disable streaming (wait for full response)")
@click.pass_context
def search_cmd(ctx: click.Context, query: str, sources: str | None,
               mode: str | None, no_stream: bool) -> None:
    """Run a search query."""
    config = ctx.obj["config"]
    _run_search(config, query, sources, mode, no_stream)


@cli.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Interactive setup to configure default provider and models."""
    config = ctx.obj["config"]
    api = PerplexicaAPI(config["url"])

    try:
        providers = api.get_providers()
    except httpx.ConnectError:
        print_error(f"Cannot connect to Perplexica at {config['url']}. Is the container running?")
        return
    except httpx.HTTPStatusError as e:
        print_error(f"API error: {e.response.status_code}")
        return
    finally:
        api.close()

    if not providers:
        print_error("No providers found. Configure providers at http://localhost:3000 first.")
        return

    console.print("\n[bold]Select a chat model provider:[/bold]")
    provider_names = [{"key": p["id"], "name": p["name"]} for p in providers]
    selected_provider = prompt_select("Provider", provider_names, key_field="key")
    if not selected_provider:
        return

    provider_id = selected_provider["key"]
    provider = next(p for p in providers if p["id"] == provider_id)

    chat_model = prompt_select("Chat Model", provider.get("chatModels", []))
    if not chat_model:
        return

    console.print("\n[bold]Select an embedding model provider:[/bold]")
    embed_provider_sel = prompt_select("Embedding Provider", provider_names, key_field="key")
    if not embed_provider_sel:
        return

    embed_provider_id = embed_provider_sel["key"]
    embed_provider = next(p for p in providers if p["id"] == embed_provider_id)

    embed_model = prompt_select("Embedding Model", embed_provider.get("embeddingModels", []))
    if not embed_model:
        return

    config["chat_model"] = {"provider_id": provider_id, "key": chat_model["key"]}
    config["embedding_model"] = {"provider_id": embed_provider_id, "key": embed_model["key"]}

    opt = click.prompt(
        "Default optimization mode",
        type=click.Choice(["speed", "balanced", "quality"]),
        default=config.get("optimization_mode", "balanced"),
    )
    config["optimization_mode"] = opt

    save_config(config)
    console.print("\n[bold green]Configuration saved![/bold green]")
    console.print(f"  Chat model:      [cyan]{chat_model['key']}[/cyan]")
    console.print(f"  Embedding model: [cyan]{embed_model['key']}[/cyan]")
    console.print(f"  Mode:            [cyan]{opt}[/cyan]")


@cli.command()
@click.pass_context
def models(ctx: click.Context) -> None:
    """List available providers and models."""
    config = ctx.obj["config"]
    api = PerplexicaAPI(config["url"])
    try:
        providers = api.get_providers()
        print_providers(providers)
    except httpx.ConnectError:
        print_error(f"Cannot connect to Perplexica at {config['url']}. Is the container running?")
    except httpx.HTTPStatusError as e:
        print_error(f"API error: {e.response.status_code}")
    finally:
        api.close()


@cli.command()
@click.option("--sources", "-s", default=None, help="Comma-separated sources: web,academic,discussions")
@click.option("--mode", "-m", type=click.Choice(["speed", "balanced", "quality"]), default=None,
              help="Optimization mode")
@click.pass_context
def chat(ctx: click.Context, sources: str | None, mode: str | None) -> None:
    """Interactive chat mode with conversation history."""
    config = ctx.obj["config"]

    if not is_configured(config):
        print_error("Not configured yet. Run: perplexica setup")
        return

    api = PerplexicaAPI(config["url"])
    history: list[list[str]] = []
    src_list = sources.split(",") if sources else config.get("sources", ["web"])
    opt_mode = mode or config.get("optimization_mode", "balanced")

    console.print("[bold cyan]Perplexica Chat[/bold cyan] [dim](type 'exit' or Ctrl+C to quit)[/dim]\n")

    try:
        while True:
            try:
                query = console.input("[bold green]You:[/bold green] ").strip()
            except EOFError:
                break

            if not query:
                continue
            if query.lower() in ("exit", "quit", ":q"):
                break

            console.print()
            try:
                events = api.search_stream(
                    query=query,
                    chat_model=config["chat_model"],
                    embedding_model=config["embedding_model"],
                    sources=src_list,
                    optimization_mode=opt_mode,
                    history=history if history else None,
                )
                full_message, srcs = stream_answer(events)
                print_sources(srcs)
                console.print()

                history.append(["human", query])
                history.append(["assistant", full_message])
            except httpx.ConnectError:
                print_error(f"Cannot connect to Perplexica at {config['url']}.")
            except httpx.HTTPStatusError as e:
                print_error(f"API error: {e.response.status_code}")
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
    finally:
        api.close()


def _run_search(
    config: dict, query: str, sources: str | None,
    mode: str | None, no_stream: bool,
) -> None:
    """Execute a single search query."""
    if not is_configured(config):
        print_error("Not configured yet. Run: perplexica setup")
        return

    api = PerplexicaAPI(config["url"])
    src_list = sources.split(",") if sources else config.get("sources", ["web"])
    opt_mode = mode or config.get("optimization_mode", "balanced")

    try:
        if no_stream:
            with console.status("[bold cyan]Searching...[/bold cyan]"):
                result = api.search(
                    query=query,
                    chat_model=config["chat_model"],
                    embedding_model=config["embedding_model"],
                    sources=src_list,
                    optimization_mode=opt_mode,
                )
            print_answer(result.get("message", ""))
            print_sources(result.get("sources", []))
        else:
            events = api.search_stream(
                query=query,
                chat_model=config["chat_model"],
                embedding_model=config["embedding_model"],
                sources=src_list,
                optimization_mode=opt_mode,
            )
            full_message, srcs = stream_answer(events)
            print_sources(srcs)
    except httpx.ConnectError:
        print_error(f"Cannot connect to Perplexica at {config['url']}. Is the container running?")
    except httpx.HTTPStatusError as e:
        print_error(f"API error: {e.response.status_code}")
    finally:
        api.close()


if __name__ == "__main__":
    cli()
