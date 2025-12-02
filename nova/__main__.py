# Copyright (c) 2024-2025 iiPython

# Modules
import json
from pathlib import Path

import asyncclick
from rich.console import Console

from . import __version__
from nova.engine import NovaEngine
from nova.engine.develop import DevelopmentStack

# Handle engine startup
def fetch_engine() -> NovaEngine:
    config_file = Path("nova.jsonc")
    if config_file.is_file():
        config_file = json.loads("\n".join(
            [line for line in config_file.read_text().splitlines() if line.strip()[:2] != "//"]
        ))

    else:
        rcon.print("[red bold]No nova.jsonc file was found, please create one.[/]")
        exit(1)

    return NovaEngine(config_file)

# CLI
rcon = Console()

@asyncclick.group
async def nova() -> None:
    """A lightning fast tool for building websites."""
    pass

@nova.command()
async def version() -> None:
    """Displays the current Nova CLI version."""

    rcon.print(f"[yellow bold]\U0001f680 Nova {__version__}, powered by [cyan]Uvicorn[/], [cyan]Jinja2[/], and [red]Love[/].[/]")
    rcon.print("[bright_black]GitHub: [cyan]https://github.com/iiPythonx/nova[/][/]")

@nova.command()
async def build() -> None:
    """Builds your app into servable HTML."""

    info = await fetch_engine().build()
    rcon.print(f"[green]\u2713 App built in [b]{info.time_taken * 1000:.2f}ms[/]![/]")

@nova.command()
@asyncclick.option("--host", default = "127.0.0.1", help = "Set the host to run on, defaults to 127.0.0.1.")
@asyncclick.option("--port", default = 8000, type = int, help = "Set the port to bind to, defaults to 8000.")
@asyncclick.option("--reload", is_flag = True, help = "Enables Nova's hot-reloading feature.")
@asyncclick.option("--open", is_flag = True, help = "Automatically opens the web server in your default browser.")
async def serve(host: str, port: int, reload: bool, open: bool) -> None:
    """Launches a local development server with the built app."""

    await DevelopmentStack(fetch_engine(), reload).launch(host, port, open)

# Handle launching CLI
if __name__ == "__main__":
    nova()
