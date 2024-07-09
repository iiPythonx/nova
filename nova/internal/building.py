# Copyright (c) 2024 iiPython

# Modules
import os
import re
import time
from pathlib import Path
from types import FunctionType

from rich import print
from jinja2 import Environment, FileSystemLoader, select_autoescape

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

        # Initial variable setup
        self.plugins = {}
        self.file_assocs, self.build_dependencies = {}, {}

        # Regex
        self._rgx_jinja = re.compile(r"{% \w* [\"'](\w.+)[\"'][\w ]* %}")
        self._rgx_reference = re.compile(r"<(?:link|script) (?:href|src) ?= ?[\"']([\w/.]+)[\"'].*>")

    def register_plugins(self, plugins: list) -> None:
        self.plugins |= {type(plugin).__name__: plugin for plugin in plugins}

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
                if file.split(".")[-1] not in ["j2", "jinja2", "jinja"]:
                    continue

                relative_location = (Path(path) / Path(file)).relative_to(self.source)
                destination_location = self.destination / relative_location.with_suffix(".html")
                destination_location.parent.mkdir(exist_ok = True)

                # Handle hot-reloading (if enabled)
                template_html = self.environ.get_template(str(relative_location).replace(os.sep, "/")).render(
                    relative = self.get_relative_location
                )
                if include_hot_reload:
                    template_content = (self.source / relative_location).read_text("utf8")

                    # I said Nova was fast, never said it was W3C compliant
                    template_html = template_html + "<script>(new WebSocket(`ws://${window.location.host}/_nova`)).addEventListener(\"message\",e=>{if(JSON.parse(e.data).reload.includes(window.location.pathname))window.location.reload();});</script>"

                    # Additionally, check for any path references to keep track of
                    self.build_dependencies[relative_location] = [
                        dep.lstrip("/") for dep in re.findall(self._rgx_reference, template_content) + \
                            re.findall(self._rgx_jinja, template_content)
                    ]

                # Finally, write it to the file
                destination_location.write_text(template_html)

        # Handle plugins
        for plugin in self.plugins.values():
            plugin.on_build(include_hot_reload)

    def register_file_associations(self, extension: str, callback: FunctionType) -> None:
        self.file_assocs[extension] = callback

    def get_relative_location(self, path: str) -> str:
        path = Path(path)
        if path.suffix in self.file_assocs:
            return self.file_assocs[path.suffix](path)
        
        return str(path)
