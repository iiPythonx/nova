# Copyright (c) 2024 iiPython

# Modules
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from . import encoding
from nova.internal.building import NovaBuilder

# Initialization
template_js = (Path(__file__).parents[1] / "assets/spa.js").read_text(encoding)

# Handle plugin
class SPAPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        mapping = config["mapping"].split(":")
        self.config, self.target, self.external, (self.source, self.destination) = \
            config, config["target"], config["external"], mapping

        # Handle remapping
        self.source = builder.destination / self.source
        self.destination = builder.destination / self.destination

    def on_build(self, dev: bool) -> None:
        page_list = ", ".join([
            f"\"/{file.relative_to(self.source).with_suffix('') if file.name != 'index.html' else ''}\""
            for file in self.source.rglob("*")
            if file.is_file()
        ])
        snippet = template_js % (page_list, self.target, self.config["title"], self.config["title_sep"])
        if self.external:
            js_location = self.destination / "js/spa.js"
            js_location.parent.mkdir(parents = True, exist_ok = True)
            js_location.write_text(snippet)
            snippet = "<script src = \"/js/spa.js\" async defer>"

        else:
            snippet = f"<script>{snippet}</script>"

        # Handle iteration
        for file in self.source.rglob("*"):
            if not file.is_file():
                continue

            new_location = self.destination / (file.relative_to(self.source))
            new_location.parent.mkdir(exist_ok = True, parents = True)

            # Add JS snippet
            shutil.copy(file, new_location)
            soup = BeautifulSoup(new_location.read_text(encoding), "html.parser")
            (soup.find("body") or soup).append(BeautifulSoup(snippet, "html.parser"))
            new_location.write_text(str(soup))

            # Strip out everything except for the content
            target_data = BeautifulSoup(file.read_text(encoding), "html.parser").select_one(self.target)
            if target_data is not None:
                file.write_bytes(target_data.encode_contents())
