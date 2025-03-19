# Copyright (c) 2024 iiPython

# Modules
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from . import Plugin
from nova import __encoding__

# Initialization
template_js = (Path(__file__).parents[1] / "assets/spa.js").read_text(__encoding__)

# Handle plugin
class SPAPlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        mapping = self.config["mapping"].split(":")
        self.config, self.target, self.external, (self.source, self.destination) = \
            self.config, self.config["target"], self.config.get("external"), mapping

        self.write = not self.config.get("noscript")

        # Handle remapping
        self.source = self.builder.destination / self.source
        self.destination = self.builder.destination / self.destination

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

        self._push_log(3, "+", f"Pages: {page_list}")

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
            target = BeautifulSoup(file.read_text(__encoding__), "lxml").select_one(self.target)
            if target is not None:
                file.write_bytes(target.encode_contents())
