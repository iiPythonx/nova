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

# from rich import print

from .building import NovaBuilder
from .hot_reload import attach_hot_reloading

# Methods
async def create_app(host: str, port: int, handler: typing.Callable, builder: NovaBuilder) -> None:
    def process_request(connection, request):
        if request.path != "/_nova":
            destination_file = builder.destination / Path(request.path[1:])
            if not destination_file.is_relative_to(builder.destination):
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
        async with serve(handler, host, port, process_request = process_request) as ws:
            await ws.serve_forever()

    except asyncio.CancelledError:
        return

async def start_stack(host, port, reload, open, builder: NovaBuilder) -> None:
    clients = set()
    async def handler(websocket) -> None:
        clients.add(websocket)
        try:
            await websocket.wait_closed()

        finally:
            clients.remove(websocket)

    async def broadcast(data: typing.Any) -> None:
        for client in clients:
            await client.send(json.dumps(data))

    async def kill() -> None:
        task.cancel()
        for client in clients.copy():
            await client.close()

    if reload:
        asyncio.create_task(attach_hot_reloading(builder, kill, broadcast))

    if open:
        webbrowser.open(f"http://{'localhost' if host == '0.0.0.0' else host}:{port}", 2)

    task = asyncio.create_task(create_app(host, port, handler, builder))
    await task
