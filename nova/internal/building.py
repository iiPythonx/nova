# Copyright (c) 2024 iiPython

# Modules
import os
import re
import time
import shlex
import typing
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Handle loading plugins in the correct order
plugin_load_order = ["static", "sass", "typescript", "spa", "nonce", "minify"]

# Main class
class NovaBuilder:
    def __init__(self, source: Path, destination: Path, build_exclude: list[str], after_build_command: typing.Optional[str]) -> None:
        self.source, self.destination = source, destination
        self.destination.mkdir(exist_ok = True)

        self.build_exclude = build_exclude
        self.after_build_command = after_build_command if (after_build_command or "").strip() else None

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
        self._rgx_reference = re.compile(r"<(?:link|script).* (?:href|src) ?= ?[\"']([\w/.]+)[\"'].*>")

    def register_plugins(self, plugins: list) -> None:
        self.plugins |= {type(plugin).__name__: plugin for plugin in plugins}

    def wrapped_build(self, *args, **kwargs) -> float:
        start = time.time()
        self.perform_build(*args, **kwargs)
        return round((time.time() - start) * 1000, 2)

    def perform_build(
        self,
        include_hot_reload: bool = False
    ) -> None:
        for file in self.source.rglob("*"):
            if not (
                file.is_file() and
                file.suffix in [".html", ".j2", ".jinja", ".jinja2"] and
                file.relative_to(self.source).parts[0] not in self.build_exclude
            ):
                continue

            relative_location = file.relative_to(self.source)
            destination_location = self.destination / relative_location.with_suffix(".html")
            destination_location.parent.mkdir(exist_ok = True)

            # Handle hot-reloading (if enabled)
            template_html = self.environ.get_template(str(relative_location).replace(os.sep, "/")).render(
                relative = self.get_relative_location
            )
            if include_hot_reload:
                template_content = (self.source / relative_location).read_text("utf8")

                # I said Nova was fast, never said it was W3C compliant
                template_html += "<script>(new WebSocket(`ws://${window.location.host}/_nova`)).addEventListener(\"message\",e=>{if(JSON.parse(e.data).includes(window.location.pathname))window.location.reload();});</script>"

                # Additionally, check for any path references to keep track of
                self.build_dependencies[relative_location] = [
                    str(relative_location.parent / Path(dep)) if dep.startswith(".") else dep.lstrip("/")
                    for dep in re.findall(self._rgx_reference, template_content) + \
                        re.findall(self._rgx_jinja, template_content)
                ]

            # Finally, write it to the file
            destination_location.write_text(template_html)

        # Handle plugins
        for plugin, _ in sorted([
            (plugin, plugin_load_order.index(name.lower().removesuffix("plugin")))
            for name, plugin in self.plugins.items()
        ], key = lambda p: p[1]):
            plugin.on_build(include_hot_reload)

        # Handle running additional commands
        if self.after_build_command is not None:
            subprocess.run(shlex.split(self.after_build_command))

    def register_file_associations(self, extension: str, callback: typing.Callable) -> None:
        self.file_assocs[extension] = callback

    def get_relative_location(self, path: Path | str) -> str:
        if isinstance(path, str):
            path = Path(path)

        if path.suffix in self.file_assocs:
            return self.file_assocs[path.suffix](path)
        
        return str(path)
