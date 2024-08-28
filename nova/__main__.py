# Copyright (c) 2024 iiPython

# Modules
import toml
import webbrowser
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
    config = toml.loads(config_file.read_text(encoding))

    # Setup building
    mapping = config["project"]["mapping"].split(":")
    builder = NovaBuilder(
        Path(mapping[0]).absolute(),
        Path(mapping[1]).absolute()
    )

    # Initialize plugins
    active_plugins = [fetch_plugin("static")(builder, {})]  # type: ignore
    for plugin, config in config.get("plugins", {}).items():
        active_plugins.append(fetch_plugin(plugin)(builder, config))  # type: ignore

    builder.register_plugins(active_plugins)

    # Link up config-needing commands
    @nova.command()
    def build() -> None:
        """Builds your app into servable HTML."""
        builder.wrapped_build()

    @nova.command()
    @click.option("--host", default = "0.0.0.0", help = "Gives socketify a specified host to run on, defaults to 0.0.0.0.")
    @click.option("--port", default = 8000, type = int, help = "Gives socketify a specified port to bind to, defaults to 8000.")
    @click.option("--reload", is_flag = True, help = "Enables Nova's hot-reloading feature.")
    @click.option("--open", is_flag = True, help = "Automatically opens the web server in your default browser.")
    def serve(host: str, port: int, reload: bool, open: bool) -> None:
        """Launches a local development server with the built app."""
        from .internal.routing import create_app
        from .internal.features import attach_hot_reloading

        builder.wrapped_build(include_hot_reload = reload)

        # Handle app
        app = create_app(host, port, builder)
        if reload:
            attach_hot_reloading(app, builder)

        if open:
            webbrowser.open(f"http://{'localhost' if host == '0.0.0.0' else host}:{port}", 2)

        app.run()

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
        config_file.write_text(toml.dumps({"project": {"mapping": f"{source_location}:{destination_location}"}}))

# Handle launching CLI
if __name__ == "__main__":
    nova()
