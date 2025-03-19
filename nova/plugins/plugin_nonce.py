# Copyright (c) 2024 iiPython

# Modules
from bs4 import BeautifulSoup

from nova import __encoding__
from . import Plugin

# Handle plugin
class NoncePlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.nonce = self.config["nonce"]
        self.destination = self.builder.destination

    def on_build(self, dev: bool) -> None:
        if dev:
            return

        for file in self.destination.rglob("*"):
            if file.suffix != ".html":
                continue

            root = BeautifulSoup(file.read_text(__encoding__), "lxml")
            for element in root.select("script, link, style"):
                if element.name == "link" and element.get("rel") != ["stylesheet"]:
                    continue

                element["nonce"] = self.nonce

            file.write_text(str(root))  # type: ignore
