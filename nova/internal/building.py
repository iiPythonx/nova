# Copyright (c) 2024 iiPython

# Modules
import os
import time
from pathlib import Path

from rich import print
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Initialization
hotreload_js_snippet = """
(new WebSocket(`ws://${window.location.host}/_nova`)).addEventListener("message", (e) => {
    if (JSON.parse(e.data).reload.includes(window.location.pathname)) window.location.reload();
});
""".strip()

# Main class
class NovaBuilder():
    def __init__(self, source: Path, destination: Path) -> None:
        self.source, self.destination = source, destination
        self.destination.mkdir(exist_ok = True)

        # Create Jinja2 environment
        self.environ = Environment(
            loader = FileSystemLoader(source),
            autoescape = select_autoescape()
        )

        # Initial plugins
        self.plugins = []

    def register_plugins(self, plugins: list) -> None:
        self.plugins += plugins

    def wrapped_build(self, *args, **kwargs) -> None:
        start = time.time()
        self.perform_build(*args, **kwargs)
        print(f"[green]\u2713 App built in [bold]{round((time.time() - start) * 1000, 2)}ms[/]![/]")

    def perform_build(
        self,
        include_hot_reload: bool = False
    ) -> None:
        for path, _, files in os.walk(self.source):
            for file in files:
                if not file.endswith(".jinja2"):
                    continue

                relative_location = (Path(path) / Path(file)).relative_to(self.source)
                destination_location = self.destination / relative_location.with_suffix(".html")
                destination_location.parent.mkdir(exist_ok = True)

                # Handle hot-reloading JS (if enabled)
                template_html = self.environ.get_template(str(relative_location)).render()
                if include_hot_reload:

                    # I said Nova was fast, never said it was W3C compliant
                    template_html = f"<script>{hotreload_js_snippet}</script>\n{template_html}"

                # Finally, write it to the file
                destination_location.write_text(template_html)

        # Handle plugins
        for plugin in self.plugins:
            plugin.on_build(include_hot_reload)
