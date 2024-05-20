# Copyright (c) 2024 iiPython

# Modules
import os
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

from nova.internal.building import NovaBuilder

# JS template
template_js = """const pages = [%s];
const length = location.origin.length;
const cache = {};
for (const link of document.getElementsByTagName("a")) {
    const relative = link.href.slice(length);
    if (!pages.includes(relative)) continue;
    const load_page = async () => {
        if (cache[relative]) return;
        cache[relative] = await (await fetch(`/pages${relative === '/' ? '/index' : relative}`)).text();
        removeEventListener("mouseover", load_page);
    };
    link.addEventListener("mouseover", load_page);
    link.addEventListener("click", (e) => {
        e.preventDefault();
        const title = relative.slice(1);
        document.title = `%s${title && ('%s' + title[0].toUpperCase() + title.slice(1))}`;
        document.querySelector("%s").innerHTML = cache[relative];
        history.pushState(null, document.title, relative);
    });
}"""

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
            for file in self.source.iterdir()
        ])
        snippet = template_js % (page_list, self.config["title"], self.config["title_sep"], self.target)
        if self.external:
            js_location = self.destination / "js/spa.js"
            js_location.parent.mkdir(parents = True, exist_ok = True)
            js_location.write_text(snippet)
            snippet = "<script src = \"/js/spa.js\" async defer>"

        else:
            snippet = f"<script>{snippet}</script>"

        # Handle iteration
        for path, _, files in os.walk(self.source):
            for file in files:
                full_path = Path(path) / Path(file)
                new_location = self.destination / (full_path.relative_to(self.source))

                # Add JS snippet
                shutil.copy(full_path, new_location)
                soup = BeautifulSoup(new_location.read_text(), "html.parser")
                (soup.find("body") or soup).append(BeautifulSoup(snippet, "html.parser"))
                new_location.write_text(str(soup))

                # Strip out everything except for the content
                target_data = BeautifulSoup(full_path.read_text(), "html.parser").select_one(self.target)
                if target_data is not None:
                    full_path.write_bytes(target_data.encode_contents())
