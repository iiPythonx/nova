# Copyright (c) 2024 iiPython

# Modules
from bs4 import BeautifulSoup

from . import Plugin

# Handle plugin
class NoncePlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.nonce = self.config["nonce"]
        self.output = self.engine.config.output

    def build(self, dev: bool) -> None:
        if dev:
            return

        for file in self.output.rglob("*"):
            if file.suffix != ".html":
                continue

            root = BeautifulSoup(file.read_text(), "lxml")
            for element in root.select("script, link, style"):
                if element.name == "link" and element.get("rel") != ["stylesheet"]:
                    continue

                element["nonce"] = self.nonce

            file.write_text(str(root))  # type: ignore
