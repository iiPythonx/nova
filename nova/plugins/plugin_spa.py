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
class SPAPlugin:
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        mapping = config["mapping"].split(":")
        self.config, self.target, self.external, (self.source, self.destination) = \
            config, config["target"], config.get("external"), mapping

        self.write = not config.get("noscript")

        # Handle remapping
        self.source = builder.destination / self.source
        self.destination = builder.destination / self.destination

        # Handle caching
        self._cached_files = None

    def on_build(self, dev: bool) -> None:
        files = [file for file in self.source.rglob("*") if file.is_file()]
        page_list = ", ".join([
            f"\"/{file.relative_to(self.source).with_suffix('') if file.name != 'index.html' else ''}\""
            for file in files
        ])
        snippet = template_js % (page_list, self.target, self.config["title"], self.config["title_sep"])
        if self.external and self.write:
            js_location = self.destination / "js/spa.js"
            js_location.parent.mkdir(parents = True, exist_ok = True)
            js_location.write_text(snippet)
            snippet = {"src": "/js/spa.js", "async": "", "defer": ""}

        else:
            snippet = {"string": snippet}

        # Handle iteration
        for file in self.source.rglob("*"):
            if not file.is_file():
                continue

            new_location = self.destination / (file.relative_to(self.source))
            new_location.parent.mkdir(exist_ok = True, parents = True)

            # Add JS snippet
            shutil.copy(file, new_location)
            if self.write:
                root = BeautifulSoup(new_location.read_text(), "lxml")
                (root.find("body") or root).append(root.new_tag("script", **snippet))  # type: ignore
                new_location.write_text(str(root))

            # Strip out everything except for the content
            target = BeautifulSoup(file.read_text(encoding), "lxml").select_one(self.target)
            if target is not None:
                file.write_bytes(target.encode_contents())
