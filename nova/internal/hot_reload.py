# Copyright (c) 2024 iiPython

# Modules
import signal
import typing
import asyncio
from pathlib import Path
from threading import Event

from watchfiles import awatch

from .building import NovaBuilder

# Handle
class FileAssociator:
    def __init__(self, builder: NovaBuilder) -> None:
        self.spa = builder.plugins.get("SPAPlugin")
        self.builder = builder

        # Handle path conversion
        self.convert_path = lambda path: path
        if self.spa is not None:
            self.spa_relative = self.spa.source.relative_to(builder.destination)
            self.convert_path = self._convert_path

    def _convert_path(self, path: Path) -> Path:
        return path.relative_to(self.spa_relative) \
            if path.is_relative_to(self.spa_relative) else path

    def calculate_reloads(self, relative_path: Path) -> list[Path]:
        reloads = []

        # Check if this change is part of a file dependency (ie. css or js)
        if relative_path.suffix in self.builder.file_assocs:
            check_path = self.builder.file_assocs[relative_path.suffix](relative_path)
            for path, dependencies in self.builder.build_dependencies.items():
                if check_path in dependencies:
                    reloads.append(path)

        else:
            def recurse(search_path: str, reloads: list = []) -> list:
                for path, dependencies in self.builder.build_dependencies.items():
                    if search_path.removeprefix("static/") in dependencies:
                        reloads.append(self.convert_path(path))
                        recurse(str(path), reloads)

                return reloads

            reloads = recurse(str(relative_path))

        if relative_path.suffix in [".jinja2", ".jinja", ".j2"] and relative_path not in reloads:
            reloads.append(self.convert_path(relative_path))

        return reloads

# Main attachment
async def attach_hot_reloading(
    builder: NovaBuilder,
    kill: typing.Callable,
    broadcast: typing.Callable
) -> None:
    stop_event = Event()
    def handle_sigint(sig, frame):
        stop_event.set()
        asyncio.create_task(kill())

    signal.signal(signal.SIGINT, handle_sigint)

    associator = FileAssociator(builder)
    async for changes in awatch(builder.source, stop_event = stop_event):
        builder.wrapped_build(include_hot_reload = True)

        # Convert paths to relative
        paths = []
        for change in changes:
            for page in associator.calculate_reloads(Path(change[1]).relative_to(builder.source)):
                clean = page.with_suffix("")
                paths.append(f"/{str(clean.parent) + '/' if str(clean.parent) != '.' else ''}{clean.name if clean.name != 'index' else ''}")

        await broadcast(paths)
