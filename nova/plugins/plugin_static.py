# Copyright (c) 2024 iiPython

# Modules
import os
import shutil
import atexit
from pathlib import Path

from nova.internal.building import NovaBuilder

# Handle plugin
class StaticPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.source, self.destination, self.config = \
            builder.source, builder.destination, config

        # Setup file paths
        self.paths = [
            (self.source / path, self.destination / path)
            for path in self.config.get("paths", [])
        ]

        # Hooks
        atexit.register(self.ensure_symlink_removal)

    def remove(self, path: Path) -> None:
        if path.is_symlink():
            return path.unlink(missing_ok = True)

        elif not path.exists():
            return

        (shutil.rmtree if path.is_dir() else os.remove)(path)

    def on_build(self, dev: bool) -> None:
        for source, destination in self.paths:
            if not source.exists():
                self.remove(destination)
                continue

            elif dev:
                if destination.is_symlink():
                    continue

                elif destination.exists():
                    self.remove(destination)

                os.symlink(source, destination)

            else:
                if destination.exists():
                    self.remove(destination)

                (shutil.copytree if source.is_dir() else shutil.copy)(source, destination)

    def ensure_symlink_removal(self) -> None:
        for source, destination in self.paths:
            if destination.is_symlink():
                self.remove(destination)
