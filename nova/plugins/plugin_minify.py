# Copyright (c) 2024 iiPython

# Modules
import subprocess
from pathlib import Path

from . import rcon
from .binaries import fetch_binary

from nova.internal.building import NovaBuilder

# Handle plugin
class MinifyPlugin:
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.builder, self.config = builder, config

        # Load executables
        self.mapping = {
            ".js":   {"func": self._minify_js,   "reqs": ["bun", "uglifyjs"]},
            ".css":  {"func": self._minify_css,  "reqs": ["bun", "csso"]},
            ".html": {"func": self._minify_html, "reqs": ["minhtml"]}
        }

        self.exec = {}
        for suffix in config["suffixes"]:
            if suffix not in self.mapping:
                rcon.print(f"[yellow]\u26a0  Minification file type unknown: '{suffix}'.[/]")

            for executable in self.mapping[suffix]["reqs"]:
                self.exec[executable] = fetch_binary(executable)

    def on_build(self, dev: bool) -> None:
        if dev and not self.config.get("minify_dev"):
            return  # Minification is disabled in development

        suffix_list = {}
        for file in self.builder.destination.rglob("*"):
            if file.suffix not in self.mapping or file.suffix not in self.config["suffixes"]:
                continue

            if file.suffix not in suffix_list:
                suffix_list[file.suffix] = []

            suffix_list[file.suffix].append(file)

        for suffix, files in suffix_list.items():
            self.mapping[suffix]["func"](files)

    # Minification steps
    def _minify_js(self, files: list[Path]) -> None:
        subprocess.run([
            self.exec["bun"], self.exec["uglifyjs"],
            "--rename", "--toplevel", "-c", "-m",

            # Yes, I'm using development options to shave hundreds of milliseconds
            # off minification time, what are you gonna do about it?
            "--in-situ", *files
        ], stdout = subprocess.DEVNULL)

    def _minify_css(self, files: list[Path]) -> None:
        for file in files:

            # I'll find a way to perform minification all in one step eventually
            # for now csso will stick with a loop
            subprocess.run([self.exec["bun"], self.exec["csso"], "-i", file, "-o", file])

    def _minify_html(self, files: list[Path]) -> None:
        subprocess.run([
            self.exec["minhtml"],

            # Attempt to still conform to specifications
            "--keep-spaces-between-attributes",
            "--do-not-minify-doctype", "--keep-closing-tags", "--keep-html-and-head-opening-tags",

            # List of HTML files
            *files
        ], stdout = subprocess.DEVNULL)
