# Copyright (c) 2024 iiPython

# Modules
import shutil
import subprocess
from pathlib import Path

import minify_html

from . import rcon, encoding
from .modules import rjsmin, rcssmin
from nova.internal.building import NovaBuilder

# Plugin defaults
# If you need to adjust these, you should do so in nova.json, not here.
# https://docs.rs/minify-html/latest/minify_html/struct.Cfg.html
config_defaults = {

    # wilsonzlin/minify-js does not work correctly for most use cases
    # once it's stable and working, i will reenable this by default
    "minify_js": False,  

    # the css minifier is also buggy but not as bad so i'll leave it on
    "minify_css": True,

    # everything else is to keep the minifier from doing anything too crazy
    # overwrite stuff in the config if you're ok with breaking w3c compliance
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

        # Handle method switching
        self.mapping = {
            ".js": self._minify_js_native,
            ".css": self._minify_css_native,
            ".html": self._minify_html
        }

        method_map, methods = {"js": "uglifyjs", "css": "csso"}, config.get("methods", {})
        for method, option in methods.items():
            if method not in method_map:
                rcon.print(f"[yellow]\u26a0  Minification file type unknown: '{method}'.[/]")

            elif option == "external" and not shutil.which(method_map[method]):
                rcon.print(f"[yellow]\u26a0  The minify plugin requires {method_map[method]} in order to perform {method.upper()} minification.[/]")

            elif option not in ["external", "native"]:
                rcon.print(f"[yellow]\u26a0  Minification type for {method.upper()} must be 'external' or 'native'.[/]")

            else:
                self.mapping[f".{method}"] = getattr(self, f"_minify_{method}_{option}")

    def on_build(self, dev: bool) -> None:
        if dev and not self.config.get("minify_dev"):
            return  # Minification is disabled in development

        for file in self.builder.destination.rglob("*"):
            if file.suffix not in self.config["suffixes"]:
                continue

            self.mapping[file.suffix](file)

    # Minification steps
    def _minify_js_native(self, path: Path) -> None:
        path.write_text(rjsmin.jsmin(path.read_text(encoding)))

    def _minify_js_external(self, path: Path) -> None:
        subprocess.run(["uglifyjs", path, "-c", "-m", "-o", path])

    def _minify_css_native(self, path: Path) -> None:
        path.write_text(rcssmin.cssmin(path.read_text(encoding)))

    def _minify_css_external(self, path: Path) -> None:
        subprocess.run(["csso", "-i", path, "-o", path])

    def _minify_html(self, path: Path) -> None:
        path.write_text(minify_html.minify(path.read_text(encoding), **self.options))
