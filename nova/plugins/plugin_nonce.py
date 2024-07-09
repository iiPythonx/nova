# Copyright (c) 2024 iiPython

# Modules
from bs4 import BeautifulSoup

from . import encoding
from nova.internal.building import NovaBuilder

# Handle plugin
class NoncePlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.nonce = config["nonce"]
        self.destination = builder.destination

    def on_build(self, dev: bool) -> None:
        if dev:
            return

        for file in self.destination.rglob("*"):
            if file.suffix != ".html":
                continue

            content = BeautifulSoup(file.read_text(encoding), "html.parser")
            for object in content.find_all(["script", "link", "style"]):
                if object.name == "link" and object.get("rel") != ["stylesheet"]:
                    continue

                object["nonce"] = self.nonce

            file.write_text(str(content))
