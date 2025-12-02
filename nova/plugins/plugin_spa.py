# Copyright (c) 2024 iiPython

# Modules
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from . import Plugin

# Initialization
SPA_JS_TEMPLATE = (Path(__file__).parents[1] / "assets/spa.js").read_text()

# Handle plugin
class SPAPlugin(Plugin):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.source = self.engine.config.output / self.config["source"]
        self.output = self.engine.config.output / self.config["output"]

        self.element, self.external = self.config["element"], self.config.get("external")
        self.add_script = self.config.get("add_script", True)

        # Handle caching
        self._cached_files = None

    def build(self, dev: bool) -> None:
        files = [file for file in self.source.rglob("*") if file.is_file()]
        page_list = ", ".join([
            f"\"/{file.relative_to(self.source).with_suffix('') if file.name != 'index.html' else ''}\""
            for file in files
        ])
        title, title_separator = self.config["title"]
        snippet = SPA_JS_TEMPLATE % (page_list, self.element, title, title_separator)
        if self.external and self.add_script:
            js_location = self.output / "js/spa.js"
            js_location.parent.mkdir(parents = True, exist_ok = True)
            js_location.write_text(snippet)
            snippet = {"src": "/js/spa.js", "async": "", "defer": ""}

        else:
            snippet = {"string": snippet}

        # Handle iteration
        for file in self.source.rglob("*"):
            if not file.is_file():
                continue

            new_location = self.output / (file.relative_to(self.source))
            new_location.parent.mkdir(exist_ok = True, parents = True)

            # Add JS snippet
            shutil.copy(file, new_location)
            if self.add_script:
                root = BeautifulSoup(new_location.read_text(), "lxml")
                (root.find("body") or root).append(root.new_tag("script", **snippet))  # type: ignore
                new_location.write_text(str(root))

            # Strip out everything except for the content
            target = BeautifulSoup(file.read_text(), "lxml").select_one(self.element)
            if target is not None:
                file.write_bytes(target.encode_contents())
