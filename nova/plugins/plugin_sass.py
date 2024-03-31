# Copyright (c) 2024 iiPython

# Modules
import subprocess
from . import StaticFileBasedBuilder

# Handle plugin
class SassPlugin(StaticFileBasedBuilder):
    def __init__(self, *args) -> None:
        super().__init__(
            (".scss", ".sass"),
            ".css",
            "scss:css",
            {"linux": "sass", "windows": "sass.bat"},
            *args
        )

    def on_build(self, dev: bool) -> None:
        subprocess.run([
            self.build_binary,
            ":".join([str(self.source), str(self.destination)]),
            "-s",
            self.config.get("style", "expanded"),
            "--no-source-map"
        ])
