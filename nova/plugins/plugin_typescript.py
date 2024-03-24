# Copyright (c) 2024 iiPython

# Modules
import os
import platform
import subprocess
from pathlib import Path

from nova.internal.building import NovaBuilder

# Handle plugin
class TypescriptPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.source, self.destination = builder.source, builder.destination

        builder.register_file_associations(".ts", self.patch_filename)

        # Load mappings
        self.config = config
        self.mapping = self.config.get("mapping", "ts:js").split(":")

        # Adjust the source and destination to match the mapping
        self.source = self.source / self.mapping[0]
        self.destination = self.destination / self.mapping[1]

        # Locate the appropriate binary
        system = platform.system().lower()
        self.swc_binary = Path(__file__).parent / "binaries" / system / ("swc" if system == "linux" else "swc.exe")

    def on_build(self, dev: bool) -> None:
        for path, _, files in os.walk(self.source):
            for file in files:
                path = Path(path)
                subprocess.run([
                    self.swc_binary,
                    "compile",
                    path / file,
                    "--out-file",
                    self.destination / path.relative_to(self.source) / file.replace(".ts", ".js")
                ])

    def patch_filename(self, filename: Path) -> str:
        if filename.parents[-2].name != self.mapping[0]:  # Not our problem
            return str(filename)
        
        return str(Path(os.sep.join([self.mapping[1]] + str(filename).split(os.sep)[1:])).with_suffix(".js"))
