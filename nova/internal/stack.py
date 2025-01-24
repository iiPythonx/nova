# Copyright (c) 2024-2025 iiPython

# Modules
import json
import typing
import signal
import asyncio
import mimetypes
import traceback
import webbrowser
from pathlib import Path
from threading import Event
from http import HTTPStatus

from watchfiles import awatch
from websockets.http11 import Response
from websockets.asyncio.server import serve
from websockets.datastructures import Headers

from .building import NovaBuilder
from .interface import Interface

# Auto-reload
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

# Methods
class Stack:
    def __init__(self, host: str, port: int, auto_reload: bool, auto_open: bool, build_instance: NovaBuilder) -> None:
        self.host, self.port = host, port
        self.auto_reload, self.auto_open = auto_reload, auto_open
        self.build_instance = build_instance

        # Create a shared instance of the interface
        self.interface = Interface()

        # Handle connections
        self.clients = set()

    def build(self) -> None | float:
        try:
            return self.build_instance.wrapped_build(include_hot_reload = self.auto_reload)

        except Exception as e:
            frames = traceback.extract_tb(e.__traceback__)
            self.interface.update_last_change(error = f"\nFollowing code:\n    > [b]{frames[-2][3]}[/]\n\n[red]{e}[/]")
            return None

    async def create_app(self, handler: typing.Callable) -> None:
        def process_request(connection, request):
            if request.path != "/_nova":
                self.interface.update_log("Request", request.path)
                destination_file = self.build_instance.destination / Path(request.path[1:])
                if not destination_file.is_relative_to(self.build_instance.destination):
                    return connection.respond(HTTPStatus.UNAUTHORIZED, "Nuh uh.\n")

                elif destination_file.is_dir():
                    destination_file = destination_file / "index.html"

                final_path = destination_file.with_suffix(".html")
                if not final_path.is_file():
                    final_path = destination_file

                if not final_path.is_file():
                    return connection.respond(HTTPStatus.NOT_FOUND, "File not found.\n")

                content_type = mimetypes.guess_file_type(final_path)[0]
                return Response(
                    HTTPStatus.OK, "OK",
                    Headers({"Content-Type": content_type} if content_type is not None else {}),
                    final_path.read_bytes()
                )

        try:
            async with serve(handler, self.host, self.port, process_request = process_request) as ws:
                await ws.serve_forever()

        except asyncio.CancelledError:
            return

    async def broadcast(self, data: typing.Any) -> None:
        self.interface.update_log("Broadcast", json.dumps(data))
        for client in self.clients:
            await client.send(json.dumps(data))

    async def kill(self) -> None:
        self.task.cancel()
        for client in self.clients.copy():
            await client.close()

    async def start(self) -> None:
        async def handler(websocket) -> None:
            self.clients.add(websocket)
            try:
                self.interface.update_general(self.auto_reload, len(self.clients))
                self.interface.update_log("Connection", "Client connected!")
                await websocket.wait_closed()

            finally:
                self.clients.remove(websocket)
                self.interface.update_general(self.auto_reload, len(self.clients))
                self.interface.update_log("Connection", "Client disconnected!")

        if self.auto_reload:
            asyncio.create_task(self.attach_hot_reloading())

        if self.auto_open:
            webbrowser.open(f"http://{'localhost' if self.host == '0.0.0.0' else self.host}:{self.port}", 2)

        self.build()
        self.interface.update_general(self.auto_reload, 0)

        self.interface.update_log("General", f"Nova is running on [u]{self.host}:{self.port}[/]. Press CTRL+C to quit.")
        if self.host == "0.0.0.0":
            self.interface.update_log("General", "[red]↳ If you don't know what you're doing, binding to 0.0.0.0 is a security risk.[/]")

        self.task = asyncio.create_task(self.create_app(handler))
        await self.task

    async def attach_hot_reloading(self) -> None:
        stop_event = Event()
        def handle_sigint(sig, frame):
            stop_event.set()
            asyncio.create_task(self.kill())

        signal.signal(signal.SIGINT, handle_sigint)

        associator = FileAssociator(self.build_instance)
        async for changes in awatch(self.build_instance.source, stop_event = stop_event):
            time = self.build()
            if time is None:
                continue

            # Convert paths to relative
            paths = []
            for change in changes:
                path = Path(change[1]).relative_to(self.build_instance.source)
                for page in associator.calculate_reloads(path):
                    clean = page.with_suffix("")
                    paths.append(f"/{str(clean.parent) + '/' if str(clean.parent) != '.' else ''}{clean.name if clean.name != 'index' else ''}")

            await self.broadcast(paths)
            self.interface.update_last_change(
                str(path), time, paths,  # type: ignore
                str(self.build_instance.source.relative_to(Path.cwd())),
                str(self.build_instance.destination.relative_to(Path.cwd()))
            )
