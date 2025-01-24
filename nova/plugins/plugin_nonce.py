# Copyright (c) 2024 iiPython

# Modules
from selectolax.lexbor import LexborHTMLParser

from . import encoding
from nova.internal.building import NovaBuilder

# Handle plugin
class NoncePlugin:
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.nonce = config["nonce"]
        self.destination = builder.destination

    def on_build(self, dev: bool) -> None:
        if dev:
            return

        for file in self.destination.rglob("*"):
            if file.suffix != ".html":
                continue

            root = LexborHTMLParser(file.read_text(encoding))
            for element in root.css("script, link, style"):
                if element.tag == "link" and element.attrs.get("rel") != "stylesheet":
                    continue

                element.attrs["nonce"] = self.nonce

            file.write_text(root.html)  # type: ignore
