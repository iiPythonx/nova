# Copyright (c) 2024 iiPython

# Modules
import json
import signal
from pathlib import Path
from threading import Thread, Event

from watchfiles import watch
from socketify import App, WebSocket, OpCode, CompressOptions

from nova.internal import NovaBuilder

# Main attachment
def attach_hot_reloading(
    app: App,
    builder: NovaBuilder
) -> None:
    async def connect_ws(ws: WebSocket) -> None: 
        ws.subscribe("reload")

    stop_event = Event()
    signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

    def hot_reload_thread(app: App) -> None:
        for changes in watch(builder.source, stop_event = stop_event):
            builder.wrapped_build(include_hot_reload = True)

            # Calculate the relative paths and send off
            paths = []
            for change in changes:
                relative = Path(change[1]).relative_to(builder.source).with_suffix("")
                paths.append(f"/{str(relative.parent) + '/' if str(relative.parent) != '.' else ''}{relative.name if relative.name != 'index' else ''}")

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