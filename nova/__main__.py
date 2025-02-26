# Copyright (c) 2024-2025 iiPython

# Modules
import tomllib
import asyncio
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .plugins import fetch_plugin, encoding
from .internal.building import NovaBuilder

# CLI
rcon = Console()
version_string = f"\U0001f680 Nova {__version__}"

@click.group
def nova() -> None:
    """A lightning fast tool for building websites."""
    pass

@nova.command()
def version() -> None:
    """Displays the current Nova CLI version."""
    rcon.print(f"[yellow bold]{version_string}[/]")

# Initialization
config_file = Path("nova.toml")
if config_file.is_file():
    config = tomllib.loads(config_file.read_text(encoding))

    # Setup building
    mapping = config["project"]["mapping"].split(":")
    builder = NovaBuilder(
        Path(mapping[0]).absolute(),
        Path(mapping[1]).absolute(),
        config["project"].get("build-exclude") or [],
        config["project"].get("after_build_command")
    )

    # Initialize plugins
    active_plugins = [fetch_plugin("static")(builder, {})]  # type: ignore
    for plugin, plugin_config in config.get("plugins", {}).items():
        active_plugins.append(fetch_plugin(plugin)(builder, plugin_config))  # type: ignore

    builder.register_plugins(active_plugins)

    # Link up config-needing commands
    @nova.command()
    def build() -> None:
        """Builds your app into servable HTML."""
        rcon.print(f"[green]\u2713 App built in [b]{builder.wrapped_build()}ms[/]![/]")

    @nova.command()
    @click.option("--host", default = "127.0.0.1", help = "Set the host to run on, defaults to 127.0.0.1.")
    @click.option("--port", default = 8000, type = int, help = "Set the port to bind to, defaults to 8000.")
    @click.option("--reload", is_flag = True, help = "Enables Nova's hot-reloading feature.")
    @click.option("--open", is_flag = True, help = "Automatically opens the web server in your default browser.")
    def serve(host: str, port: int, reload: bool, open: bool) -> None:
        """Launches a local development server with the built app."""
        from nova.internal.stack import Stack

        flags = config.get("flags", {})
        asyncio.run(Stack(
            host,
            port,
            reload or flags.get("reload"),
            open or flags.get("open"),
            builder
        ).start())

else:

    @nova.command()
    def init() -> None:
        """Initializes a new Nova project in the current directory."""
        rcon.print(f"[yellow bold]{version_string} | Project Initialization[/]")

        # Ask for the locations
        source_location = rcon.input("Source location (default: [green]src[/]): ") or "src"
        destination_location = rcon.input("Destination location (default: [green]dist[/]): ") or "dist"

        # Create them if they don't exist
        def check_path(path: Path) -> None:
            if not (not path.is_file() and path.parent.is_dir()):
                rcon.print(f"\n[red]> Invalid location given: '{path}'.[/]")
                exit(1)

            path.mkdir(exist_ok = True)

        check_path(Path(source_location))
        check_path(Path(destination_location))

        # Write to file
        config_file.write_text(f"[project]\nmapping = \"{source_location}:{destination_location}\"")

# Handle launching CLI
if __name__ == "__main__":
    nova()
