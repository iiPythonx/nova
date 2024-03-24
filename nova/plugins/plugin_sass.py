# Copyright (c) 2024 iiPython

# Modules
import platform
import subprocess
from pathlib import Path

from nova.internal.building import NovaBuilder

# Handle plugin
class SassPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.source, self.destination = builder.source, builder.destination

        # Load mappings
        self.config = config
        self.mapping = self.config.get("mapping", "scss:css").split(":")

        # Locate the appropriate binary
        system = platform.system().lower()
        self.sass_binary = Path(__file__).parent / "sass" / system / ("sass" if system == "linux" else "sass.bat")

    def on_build(self, dev: bool) -> None:
        subprocess.run([
            self.sass_binary,
            ":".join([str(self.source / self.mapping[0]), str(self.destination / self.mapping[1])]),
            "-s",
            self.config.get("style", "expanded"),
            "--no-source-map"
        ])
