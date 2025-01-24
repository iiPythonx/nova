# Copyright (c) 2024 iiPython

# Modules
import json
import typing
import asyncio
import mimetypes
import webbrowser
from pathlib import Path
from http import HTTPStatus

from websockets.http11 import Response
from websockets.asyncio.server import serve
from websockets.datastructures import Headers

from .interface import Interface
from .building import NovaBuilder
from .hot_reload import attach_hot_reloading

# Methods
class Stack:
    def __init__(self, host: str, port: int, auto_reload: bool, auto_open: bool, build_instance: NovaBuilder) -> None:
        self.host, self.port = host, port
        self.auto_reload, self.auto_open = auto_reload, auto_open
        self.build_instance = build_instance

        # Create a shared instance of the interface
        self.interface = Interface()

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

    async def start(self) -> None:
        clients = set()
        async def handler(websocket) -> None:
            clients.add(websocket)
            try:
                self.interface.update_general(self.auto_reload, len(clients))
                self.interface.update_log("Connection", "Client connected!")
                await websocket.wait_closed()

            finally:
                clients.remove(websocket)
                self.interface.update_general(self.auto_reload, len(clients))
                self.interface.update_log("Connection", "Client disconnected!")

        async def broadcast(data: typing.Any) -> None:
            self.interface.update_log("Broadcast", json.dumps(data))
            for client in clients:
                await client.send(json.dumps(data))

        async def kill() -> None:
            task.cancel()
            for client in clients.copy():
                await client.close()

        if self.auto_reload:
            asyncio.create_task(attach_hot_reloading(self.build_instance, kill, broadcast, self.interface))

        if self.auto_open:
            webbrowser.open(f"http://{'localhost' if self.host == '0.0.0.0' else self.host}:{self.port}", 2)

        self.interface.update_general(self.auto_reload, 0)
        task = asyncio.create_task(self.create_app(handler))
        await task
