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
        self.source, self.destination = \
            builder.source / "static", builder.destination

        # Hooks
        atexit.register(self.ensure_symlink_removal)

    def remove(self, path: Path) -> None:
        if path.is_symlink():
            return path.unlink(missing_ok = True)

        elif not path.exists():
            return

        (shutil.rmtree if path.is_dir() else os.remove)(path)

    def on_build(self, dev: bool) -> None:
        if not self.source.is_dir():
            return

        for source_path, _, source_files in os.walk(self.source):
            for source_file in source_files:
                source = Path(source_path) / Path(source_file)
                destination = self.destination / source.relative_to(self.source)
                if not source.exists():
                    self.remove(destination)
                    continue

                if not destination.parent.is_dir():
                    destination.parent.mkdir(parents = True)

                if dev:
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
        for file in self.destination.rglob("*"):
            if file.is_symlink():
                self.remove(file)

        for file in self.destination.rglob("*"):
            if file.is_dir() and not any([x.is_file() for x in file.rglob("*")]):
                shutil.rmtree(file)
