# Copyright (c) 2024-2025 iiPython

# Modules
import os
import shutil
import atexit
from pathlib import Path

from . import Plugin

# Handle plugin
class StaticPlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.source = self.engine.config.source / "static"
        self.output = self.engine.config.output / "static"

        # Hooks
        atexit.register(self.ensure_symlink_removal)

    def remove(self, path: Path) -> None:
        if path.is_symlink() or path.is_file():
            return path.unlink(missing_ok = True)

        elif path.is_dir():
            shutil.rmtree(path)

    def build(self, dev: bool) -> None:
        if not self.source.is_dir():
            return

        for file in self.source.rglob("*"):
            if not file.is_file():
                continue

            output = self.output / file.relative_to(self.source)
            if not file.exists():
                self.remove(output)
                continue

            if not output.parent.is_dir():
                output.parent.mkdir(parents = True)

            if dev:
                if output.is_symlink():
                    continue

                elif output.exists():
                    self.remove(output)

                os.symlink(file, output)

            else:
                if output.exists():
                    self.remove(output)

                (shutil.copytree if file.is_dir() else shutil.copy)(file, output)

    def ensure_symlink_removal(self) -> None:
        for file in self.output.rglob("*"):
            if file.is_symlink():
                self.remove(file)

        for file in self.output.rglob("*"):
            if file.is_dir() and not any([x.is_file() for x in file.rglob("*")]):
                shutil.rmtree(file)
