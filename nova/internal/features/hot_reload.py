# Copyright (c) 2024 iiPython

# Modules
import json
import signal
from typing import List
from pathlib import Path
from threading import Thread, Event

from watchfiles import watch
from socketify import App, WebSocket, OpCode, CompressOptions

from nova.internal.building import NovaBuilder

# Handle
class FileAssociator():
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

    def calculate_reloads(self, relative_path: Path) -> List[Path]:
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
                    if search_path in dependencies:
                        reloads.append(self.convert_path(path))
                        recurse(str(path), reloads)

                return reloads

            reloads = recurse(str(relative_path))

        if relative_path.suffix in [".jinja2", ".jinja", ".j2"] and relative_path not in reloads:
            reloads.append(self.convert_path(relative_path))

        return reloads

# Main attachment
def attach_hot_reloading(
    app: App,
    builder: NovaBuilder
) -> None:
    associator = FileAssociator(builder)
    async def connect_ws(ws: WebSocket) -> None: 
        ws.subscribe("reload")

    stop_event = Event()
    signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

    def hot_reload_thread(app: App) -> None:
        for changes in watch(builder.source, stop_event = stop_event):
            builder.wrapped_build(include_hot_reload = True)

            # Convert paths to relative
            paths = []
            for change in changes:
                for page in associator.calculate_reloads(Path(change[1]).relative_to(builder.source)):
                    clean = page.with_suffix("")
                    paths.append(f"/{str(clean.parent) + '/' if str(clean.parent) != '.' else ''}{clean.name if clean.name != 'index' else ''}")

            app.publish("reload", json.dumps({"reload": paths}), OpCode.TEXT)

    Thread(target = hot_reload_thread, args = [app]).start()
    app.ws(
        "/_nova",
        {
            "compression": CompressOptions.SHARED_COMPRESSOR,
            "max_payload_length": 16 * 1024 * 1024,
            "open": connect_ws
        }
    )
