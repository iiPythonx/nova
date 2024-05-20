# Copyright (c) 2024 iiPython

# Modules
from bs4 import BeautifulSoup

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
            if not file.suffix == ".html":
                continue

            content = BeautifulSoup(file.read_text(), "html.parser")
            for object in content.find_all(["script", "link", "style"]):
                if object.name == "link" and object.rel != "stylesheet":
                    continue

                object["nonce"] = self.nonce

            file.write_text(str(content))
