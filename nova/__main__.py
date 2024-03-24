# Copyright (c) 2024 iiPython

# Modules
import os
import json
import time
import signal
from pathlib import Path
from threading import Thread, Event

import click
from rich import print
from watchfiles import watch
from socketify import App, WebSocket, OpCode, CompressOptions, sendfile
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .plugins import available_plugins

# Constants
hotreload_js_snippet = """
(new WebSocket(`ws://${window.location.host}/_nova`)).addEventListener("message", (e) => {
    if (JSON.parse(e.data).reload.includes(window.location.pathname)) window.location.reload();
});
""".strip()

# Initialization
config_file = Path("nova.json")
if not config_file.is_file():
    print("[red]You don't appear to be inside of a Nova project.[/]")
    exit(1)

config = json.loads(config_file.read_text())

# Jinja2 Initialization
project_source, project_dest = Path(config["project"]["source"]).absolute(), \
    Path(config["project"]["destination"]).absolute()

project_dest.mkdir(exist_ok = True)

env = Environment(
    loader = FileSystemLoader(project_source),
    autoescape = select_autoescape()
)

# Initialize plugins
active_plugins = []
for plugin, config in config.get("plugins", {}).items():
    if plugin not in available_plugins:
        raise Exception(f"Unknown plugin name: '{plugin}'")

    active_plugins.append(available_plugins[plugin](project_source, project_dest, config))

# Handle building (outside of Click)
def perform_build(dev: bool = False) -> None:
    start = time.time()

    # Handle walking source
    for path, _, files in os.walk(project_source):
        for file in files:
            if not file.endswith(".jinja2"):
                continue

            relative_location = (Path(path) / Path(file)).relative_to(project_source)
            destination_location = project_dest / relative_location.with_suffix(".html")
            destination_location.parent.mkdir(exist_ok = True)

            # Handle hot-reloading JS (if enabled)
            template_html = env.get_template(str(relative_location)).render()
            if dev:

                # I said Nova was fast, never said it was W3C compliant
                template_html = f"<script>{hotreload_js_snippet}</script>\n{template_html}"

            # Finally, write it to the file
            destination_location.write_text(template_html)

    # Handle plugins
    for plugin in active_plugins:
        plugin.on_build(dev)

    # Show results
    print(f"[green]\u2713 App built in [bold]{round((time.time() - start) * 1000, 2)}ms[/]![/]")

# CLI
@click.group
def nova() -> None:
    """A lightning fast tool for building websites."""
    pass

@nova.command()
def build() -> None:
    """Builds your app into servable HTML."""
    perform_build()

@nova.command()
@click.option("--host", default = "0.0.0.0", help = "Gives socketify a specified host to run on, defaults to 0.0.0.0.")
@click.option("--port", default = 8000, type = int, help = "Gives socketify a specified port to bind to, defaults to 8000.")
@click.option("--dev", is_flag = True, help = "Enables Nova's hot-reloading feature.")
def serve(host: str, port: int, dev: bool) -> None:
    """Launches a local development server with the built app."""

    # Handle serving our files
    async def serve_route(res, req):
        destination_file = project_dest / Path(req.get_url()[1:])
        if not destination_file.is_relative_to(project_dest):
            return res.end("No, I don't think so.")
        
        elif destination_file.is_dir():
            destination_file = destination_file / "index.html"

        final_path = destination_file.with_suffix(".html")
        if not final_path.is_file():
            final_path = destination_file

        await sendfile(res, req, final_path)

    perform_build(dev)

    # Setup base app
    app = App()

    # Handle the dev websocket
    if dev:
        async def connect_ws(ws: WebSocket) -> None: 
            ws.subscribe("reload")

        stop_event = Event()
        signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

        def hot_reload_thread(app: App) -> None:
            for changes in watch(project_source, stop_event = stop_event):
                perform_build(True)

                # Calculate the relative paths and send off
                paths = []
                for change in changes:
                    relative = Path(change[1]).relative_to(project_source).with_suffix("")
                    paths.append(f"/{str(relative.parent) + '/' if str(relative.parent) != '.' else ''}{relative.name if relative.name != 'index' else ''}")

                app.publish("reload", json.dumps({"reload": paths}), OpCode.TEXT)

        Thread(target = hot_reload_thread, args = [app]).start()
        app.ws(
            "/_nova",
            {
                "compression": CompressOptions.SHARED_COMPRESSOR,
                "max_payload_length": 16 * 1024 * 1024,
                "open": connect_ws
            }
        )

    # Handle routing
    app.get("/*", serve_route)
    app.listen({
        "port": port,
        "host": host
    }, lambda config: print(f"[bold]\u231b Nova is listening at http://{host}:{config.port} now.[/]"))
    app.run()

# Handle launching CLI
if __name__ == "__main__":
    nova()
