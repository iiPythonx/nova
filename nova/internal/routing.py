# Copyright (c) 2024 iiPython

# Modules
from pathlib import Path

from rich import print
from socketify import App, sendfile

from .building import NovaBuilder

# Methods
def create_app(host: str, port: int, builder: NovaBuilder) -> App:

    # Handle serving our files
    async def serve_route(res, req):
        destination_file = builder.destination / Path(req.get_url()[1:])
        if not destination_file.is_relative_to(builder.destination):
            return res.end("No, I don't think so.")
        
        elif destination_file.is_dir():
            destination_file = destination_file / "index.html"

        final_path = destination_file.with_suffix(".html")
        if not final_path.is_file():
            final_path = destination_file

        await sendfile(res, req, final_path)

    # Create initial app
    app = App()
    app.get("/*", serve_route)
    app.listen({
        "port": port,
        "host": host
    }, lambda config: print(f"[bold]\u231b Nova is listening at http://{host}:{config.port} now.[/]"))
    
    # Pass back to whatever else
    return app
