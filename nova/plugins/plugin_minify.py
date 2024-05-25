# Copyright (c) 2024 iiPython

# Modules
import shutil
import subprocess
from pathlib import Path

import minify_html

from . import rcon
from nova.internal.building import NovaBuilder

# Plugin defaults
# If you need to adjust these, you should do so in nova.json, not here.
# https://docs.rs/minify-html/latest/minify_html/struct.Cfg.html
config_defaults = {
    "minify_js": False,  # Seems bugged
    "minify_css": True,
    "remove_processing_instructions": True,
    "do_not_minify_doctype": True,
    "ensure_spec_compliant_unquoted_attribute_values": True,
    "keep_spaces_between_attributes": True,
    "keep_closing_tags": True,
    "keep_html_and_head_opening_tags": True,
    "keep_comments": False
}

# Handle plugin
class MinifyPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.builder, self.config = builder, config
        self.options = config_defaults | config.get("options", {})

        self.mapping = {
            ".js": self._minify_js,
            ".css": self._minify_css,
            ".html": self._minify_html
        }

        # Check for uglifyjs
        if ".js" in self.config["suffixes"] and not shutil.which("uglifyjs"):
            rcon.print("[yellow]\u26a0  The minify plugin requires uglifyjs in order to perform JS minification.[/]")
            self.config["suffixes"].remove(".js")

    def _minify_js(self, path: Path) -> None:
        subprocess.run(["uglifyjs", path, "-c", "-m", "-o", path])

    def _minify_css(self, path: Path) -> None:
        path.write_text(minify_html.minify("<style>" + path.read_text())[8:])

    def _minify_html(self, path: Path) -> None:
        path.write_text(minify_html.minify(path.read_text(), **self.options))

    def on_build(self, dev: bool) -> None:
        if dev and not self.config.get("minify_dev"):
            return  # Minification is disabled in development

        for file in self.builder.destination.rglob("*"):
            if file.suffix not in self.config["suffixes"]:
                continue

            self.mapping[file.suffix](file)
