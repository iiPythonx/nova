# Copyright (c) 2024 iiPython

# Modules
import subprocess

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
        for file in self.source.rglob("*"):
            if not file.is_file():
                continue

            subprocess.run([
                self.build_binary,
                "compile",
                file,
                "--out-file",
                self.destination / file.with_suffix(".js").relative_to(self.source)
            ])
