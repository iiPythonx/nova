# Copyright (c) 2024 iiPython

# Modules
import json
from pathlib import Path

import click
from rich import print

from .plugins import fetch_plugin

from .internal import create_app, NovaBuilder
from .internal.features import attach_hot_reloading

# Initialization
config_file = Path("nova.json")
if not config_file.is_file():
    print("[red]You don't appear to be inside of a Nova project.[/]")
    exit(1)

config = json.loads(config_file.read_text())

# Setup building
builder = NovaBuilder(
    Path(config["project"]["source"]).absolute(),
    Path(config["project"]["destination"]).absolute()
)

# Initialize plugins
active_plugins = []
for plugin, config in config.get("plugins", {}).items():
    active_plugins.append(fetch_plugin(plugin)(builder, config))

builder.register_plugins(active_plugins)

# CLI
@click.group
def nova() -> None:
    """A lightning fast tool for building websites."""
    pass

@nova.command()
def build() -> None:
    """Builds your app into servable HTML."""
    builder.wrapped_build()

@nova.command()
@click.option("--host", default = "0.0.0.0", help = "Gives socketify a specified host to run on, defaults to 0.0.0.0.")
@click.option("--port", default = 8000, type = int, help = "Gives socketify a specified port to bind to, defaults to 8000.")
@click.option("--reload", is_flag = True, help = "Enables Nova's hot-reloading feature.")
def serve(host: str, port: int, reload: bool) -> None:
    """Launches a local development server with the built app."""
    app = create_app(host, port, builder)
    if reload:
        attach_hot_reloading(app, builder)

    app.run()

# Handle launching CLI
if __name__ == "__main__":
    nova()
