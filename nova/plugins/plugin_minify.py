# Copyright (c) 2024 iiPython

# Modules
import os
import subprocess
from pathlib import Path

from nova.internal.building import NovaBuilder

import minify_html

# Plugin defaults
# If you need to adjust these, you should do so in nova.json, not here.
# https://docs.rs/minify-html/latest/minify_html/struct.Cfg.html
config_defaults = {
    "minify_js": True,
    "minify_css": True,
    "remove_processing_instructions": True,
    "do_not_minify_doctype": True,
    "ensure_spec_compliant_unquoted_attribute_values": True,
    "keep_spaces_between_attributes": True,
    "keep_closing_tags": True,
    "keep_html_and_head_opening_tags": True,
    "keep_comments": False
}

# Handle plugin
class MinifyPlugin():
    def __init__(self, builder: NovaBuilder, config: dict) -> None:
        self.builder, self.config = builder, config
        self.options = config_defaults | config.get("options", {})

        # This is a very bad way of doing things, but this is my tool and I do what I want.
        # (and I already switched to minify-html and it's too much work to swap again)
        self.mapping = {
            ".js": "<script>", ".css": "<style>"
        }

    def on_build(self, dev: bool) -> None:
        if dev:
            return  # Minification is disabled in development

        for path, _, files in os.walk(self.builder.destination):
            path = Path(path)
            for file in files:
                file = path / Path(file)
                if file.suffix not in self.config["suffixes"]:
                    continue

                tag = self.mapping.get(file.suffix, "")
                file.write_text(minify_html.minify(tag + file.read_text(), **self.options)[len(tag):])
