# Copyright (c) 2024 iiPython

# Modules
import subprocess

from . import StaticFileBasedBuilder
from .binaries import fetch_binary

# Handle plugin
class SassPlugin(StaticFileBasedBuilder):
    def __init__(self, *args) -> None:
        super().__init__(
            (".scss", ".sass"),
            ".css",
            "scss:css",
            *args
        )
        self.build_binary = fetch_binary("sass")

    def on_build(self, dev: bool) -> None:
        subprocess.run([
            self.build_binary,
            ":".join([str(self.source), str(self.destination)]),
            "-s",
            self.config.get("style", "expanded"),
            "--no-source-map"
        ])
