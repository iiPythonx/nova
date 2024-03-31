# Copyright (c) 2024 iiPython

# Modules
import os
import subprocess
from pathlib import Path

from . import StaticFileBasedBuilder

# Handle plugin
class TypescriptPlugin(StaticFileBasedBuilder):
    def __init__(self, *args) -> None:
        super().__init__(
            (".ts",),
            ".js",
            "ts:js",
            {"linux": "swc", "windows": "swc.exe"},
            *args
        )

    def on_build(self, dev: bool) -> None:
        for path, _, files in os.walk(self.source):
            for file in files:
                path = Path(path)
                subprocess.run([
                    self.build_binary,
                    "compile",
                    path / file,
                    "--out-file",
                    self.destination / path.relative_to(self.source) / file.replace(".ts", ".js")
                ])
