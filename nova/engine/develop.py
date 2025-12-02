# Copyright (c) 2025 iiPython

# Modules
import json
import signal
import asyncio
import mimetypes
import webbrowser
from pathlib import Path

from watchfiles import awatch

from websockets.http11 import Request, Response
from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers

from nova.engine.interface import Interface

# Improved stack
class DevelopmentStack:
    def __init__(self, engine, development: bool) -> None:
        self.engine = engine
        self.clients: set[ServerConnection] = set()

        # Store interface
        self.interface = Interface()

        # Toggle flags
        self.dev_mode = development

    async def generate_websocket_app(self, host: str, port: int) -> None:
        def process_request(connection: ServerConnection, request: Request) -> Response | None:
            if request.path != "/_nova":
                target_file = self.engine.config.output / Path(request.path[1:])
                if not target_file.is_relative_to(self.engine.config.output) and target_file != self.engine.config.output:
                    return connection.respond(401, "Nuh uh.\n")

                elif target_file.is_dir():
                    target_file = target_file / "index.html"

                final_path = target_file.with_suffix(".html")
                if not final_path.is_file():
                    final_path = target_file

                if not final_path.is_file():
                    return connection.respond(404, "File not found.\n")

                content_type = mimetypes.guess_file_type(final_path)[0]
                return Response(
                    200,
                    "OK",
                    Headers({"Content-Type": content_type} if content_type is not None else {}),
                    final_path.read_bytes()
                )

        try:
            async def handle_incoming(websocket: ServerConnection) -> None:
                try:
                    self.clients.add(websocket)
                    self.interface.update_general(self.dev_mode, len(self.clients))
                    await websocket.wait_closed()

                finally:
                    self.clients.remove(websocket)
                    self.interface.update_general(self.dev_mode, len(self.clients))

            async with serve(handle_incoming, host, port, process_request = process_request) as ws:
                await ws.serve_forever()

        except asyncio.CancelledError:
            return

    async def launch(self, host: str, port: int, open: bool) -> None:
        if self.dev_mode:
            asyncio.create_task(self.attach_hot_reloading())

        if open:
            webbrowser.open(f"http://{'localhost' if host == '0.0.0.0' else host}:{port}", 2)

        await self.engine.build(self.dev_mode)
        self.interface.update_general(self.dev_mode, 0)

        self.task = asyncio.create_task(self.generate_websocket_app(host, port))
        await self.task

    async def kill(self) -> None:
        self.task.cancel()
        [await client.close() for client in self.clients.copy()]

    async def attach_hot_reloading(self) -> None:
        stop_event = asyncio.Event()
        def handle_sigint(sig, frame):
            stop_event.set()
            asyncio.create_task(self.kill())

        signal.signal(signal.SIGINT, handle_sigint)

        async for changes in awatch(self.engine.config.source, stop_event = stop_event):
            for _, file in changes:
                try:
                    info = await self.engine.build(self.dev_mode)
                    file = Path(file)

                    # Identify dependencies
                    def resolve(file: Path) -> list[Path]:
                        if file.is_relative_to(self.engine.config.static):
                            file = self.engine.config.source / file.relative_to(self.engine.config.static)

                        dependencies = info.dependencies.get(file, [])
                        for dependency in dependencies:
                            dependencies += resolve(dependency)

                        return dependencies

                    dependencies = [
                        p.relative_to(self.engine.config.source).with_suffix(".html" if p.suffix in [".j2", ".jinja", ".jinja2"] else p.suffix)
                        for p in resolve(file) + [file]
                    ]
                    for index, dep in enumerate(dependencies.copy()):
                        dependencies[index] = Path("/".join(x for x in str(dep).split("/")[1:])) if dep.is_relative_to("static") else dep

                    # Handle SPA as well
                    spa_plugin = self.engine.config.plugins.get("spa")
                    if spa_plugin is not None:
                        spa_source = spa_plugin.source.relative_to(self.engine.config.output)
                        for index, dep in enumerate(dependencies.copy()):
                            if not dep.is_relative_to(spa_source):
                                continue

                            dependencies[index] = dep.relative_to(spa_source)

                    # Broadcast
                    self.interface.update_last_change(info, str(file), deps = (str(_) for _ in dependencies))
                    for client in self.clients:
                        await client.send(json.dumps([
                            f"/{str(clean.parent) + '/' if str(clean.parent) != '.' else ''}{clean.name if clean.name != 'index' else ''}"
                            for clean in [page.with_suffix("") for page in dependencies]
                        ]))

                except Exception as e:
                    self.interface.update_last_change(None, str(file), error = e)
