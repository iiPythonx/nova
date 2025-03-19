# Copyright (c) 2024 iiPython

# Modules
import subprocess
from pathlib import Path

from . import rcon, Plugin
from .binaries import fetch_binary

# Handle plugin
class MinifyPlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.mapping = {
            ".js":   {"func": self._minify_js,   "reqs": ["bun", "uglifyjs"]},
            ".css":  {"func": self._minify_css,  "reqs": ["bun", "csso"]},
            ".html": {"func": self._minify_html, "reqs": ["minhtml"]}
        }

        self.exec = {}
        for suffix in self.config["suffixes"]:
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
    def _execute(self, segments: list[str | Path]) -> None:
        subprocess.run(segments, stdout = subprocess.DEVNULL)

        line = " ".join((str(segment.relative_to(Path.cwd())) if segment not in self.exec.values() else segment.name) if isinstance(segment, Path) else segment for segment in segments)
        self._push_log(3, "+", line if len(line) < 130 else line[:130] + " ...")

    def _minify_js(self, files: list[Path]) -> None:
        self._execute([
            self.exec["bun"], self.exec["uglifyjs"],
            "--rename", "--toplevel", "-c", "-m",

            # Yes, I'm using development options to shave hundreds of milliseconds
            # off minification time, what are you gonna do about it?
            "--in-situ", *files
        ])

    def _minify_css(self, files: list[Path]) -> None:
        for file in files:

            # I'll find a way to perform minification all in one step eventually
            # for now csso will stick with a loop
            self._execute([self.exec["bun"], self.exec["csso"], "-i", file, "-o", file])

    def _minify_html(self, files: list[Path]) -> None:
        self._execute([
            self.exec["minhtml"],

            # Attempt to still conform to specifications
            "--keep-spaces-between-attributes",
            "--do-not-minify-doctype", "--keep-closing-tags", "--keep-html-and-head-opening-tags",

            # List of HTML files
            *files
        ])
