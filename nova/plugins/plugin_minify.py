# Copyright (c) 2024 iiPython

# Modules
import shutil
import subprocess
from pathlib import Path

from . import rcon, encoding
from .modules import rjsmin, rcssmin
from .binaries import fetch_binary

from nova.internal.building import NovaBuilder

# Handle plugin
class MinifyPlugin:
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.builder, self.config = builder, config

        # Handle method switching
        self.mapping = {
            ".js": self._minify_js_native,
            ".css": self._minify_css_native,
            ".html": self._minify_html
        }

        method_map, methods = {"js": "uglifyjs", "css": "csso"}, config.get("methods", {})
        for method, option in methods.items():
            if method not in method_map:
                rcon.print(f"[yellow]\u26a0  Minification file type unknown: '{method}'.[/]")

            elif option == "external" and not shutil.which(method_map[method]):
                rcon.print(f"[yellow]\u26a0  The minify plugin requires {method_map[method]} in order to perform {method.upper()} minification.[/]")

            elif option not in ["external", "native"]:
                rcon.print(f"[yellow]\u26a0  Minification type for {method.upper()} must be 'external' or 'native'.[/]")

            else:
                self.mapping[f".{method}"] = getattr(self, f"_minify_{method}_{option}")

    def on_build(self, dev: bool) -> None:
        if dev and not self.config.get("minify_dev"):
            return  # Minification is disabled in development

        suffix_list = {}
        for file in self.builder.destination.rglob("*"):
            if file.suffix not in self.mapping:
                continue

            if file.suffix not in suffix_list:
                suffix_list[file.suffix] = []

            suffix_list[file.suffix].append(file)

        for suffix, files in suffix_list.items():
            self.mapping[suffix](files)

    # Minification steps
    def _minify_js_native(self, files: list[Path]) -> None:
        for file in files:
            file.write_text(rjsmin.jsmin(file.read_text(encoding)))  # type: ignore

    def _minify_js_external(self, files: list[Path]) -> None:
        subprocess.run([
            fetch_binary("bun"), fetch_binary("uglifyjs"),
            "--rename", "--toplevel", "-c", "-m",

            # Yes, I'm using development options to shave hundreds of milliseconds
            # off minification time, what are you gonna do about it?
            "--in-situ", *files
        ], stdout = subprocess.DEVNULL)

    def _minify_css_native(self, files: list[Path]) -> None:
        for file in files:
            file.write_text(rcssmin.cssmin(file.read_text(encoding)))  # type: ignore

    def _minify_css_external(self, files: list[Path]) -> None:
        bun, csso = fetch_binary("bun"), fetch_binary("csso")
        for file in files:

            # I'll find a way to perform minification all in one step eventually
            # for now csso will stick with a loop
            subprocess.run([bun, csso, "-i", file, "-o", file])

    def _minify_html(self, files: list[Path]) -> None:
        subprocess.run([
            fetch_binary("minhtml"),

            # Attempt to still conform to specifications
            "--keep-spaces-between-attributes",
            "--do-not-minify-doctype", "--keep-closing-tags", "--keep-html-and-head-opening-tags",

            # List of HTML files
            *files
        ], stdout = subprocess.DEVNULL)
