# Copyright (c) 2024 iiPython

# Modules
import os
import platform
import subprocess
from shutil import which
from pathlib import Path
from typing import Dict, Tuple
from types import FunctionType
from importlib import import_module

from rich.console import Console

from nova.internal.building import NovaBuilder

# Plugin specified encoding
encoding = "utf8"

# Handle plugin initialization
def plugin_load_callback(name: str, class_name: str) -> FunctionType:
    def load_plugin() -> None:
        return getattr(import_module(name, "nova.plugins"), class_name)

    return load_plugin

available_plugins = {
    "static": {
        "module": plugin_load_callback(".plugin_static", "StaticPlugin")
    },
    "sass": {
        "module": plugin_load_callback(".plugin_sass", "SassPlugin")
    },
    "typescript": {
        "module": plugin_load_callback(".plugin_typescript", "TypescriptPlugin"),
    },
    "spa": {
        "module": plugin_load_callback(".plugin_spa", "SPAPlugin"),
        "requirements": ["beautifulsoup4"]
    },
    "nonce": {
        "module": plugin_load_callback(".plugin_nonce", "NoncePlugin"),
        "requirements": ["beautifulsoup4"]
    },
    "minify": {
        "module": plugin_load_callback(".plugin_minify", "MinifyPlugin"),
        "requirements": ["minify-html"]
    }
}

# Plugin loading wrapper
rcon = Console()

def fetch_plugin(plugin_name: str) -> object:
    if plugin_name not in available_plugins:
        raise Exception(f"Invalid plugin name: '{plugin_name}'!")
    
    plugin_meta = available_plugins[plugin_name]
    try:
        return plugin_meta["module"]()
    
    except ImportError:
        if "requirements" not in plugin_meta:
            raise Exception(f"Plugin '{plugin_name}' uses modules that aren't listed as requirements!")

        rcon.print(f"[yellow]\u26a0  Plugin '{plugin_name}' requires the following packages: [bold]{', '.join(plugin_meta['requirements'])}[/].[/]")

        # Attempt to calculate the package manager in use
        available_packager = None
        for packager in [("uv", "pip install"), ("pip", "install"), ("poetry", "add")]:
            if not which(packager[0]):
                continue

            available_packager = packager
            break

        if available_packager is None:
            rcon.print("[bold]In order to use the plugin, please install them.[/]")
            exit(1)

        installation_command = f"{' '.join(available_packager)} {' '.join(plugin_meta['requirements'])}"

        # Prompt them
        if rcon.input("[bold]Would you like to install them automatically ([green]y[/]/[red]N[/])?[/] ").lower() in ["y", "yes"]:
            subprocess.run(installation_command.split(" "))
            return fetch_plugin(plugin_name)

        else:
            rcon.print(f"Running '{installation_command}' should install them on your system.")
            exit(1)

# Helping class for repetitive external tool plugins
class StaticFileBasedBuilder():
    def __init__(
        self,
        file_associations: Tuple[str],
        destination_extension: str,
        default_mapping: str,
        build_binaries: Dict[str, str],
        builder: NovaBuilder,
        config: dict
    ) -> None:
        self.destination_extension = destination_extension
        self.source, self.destination = builder.source, builder.destination

        for association in file_associations:
            builder.register_file_associations(association, self.patch_filename)

        # Load mappings
        self.config = config
        self.mapping = self.config.get("mapping", default_mapping).split(":")

        # Adjust the source and destination to match the mapping
        self.source = self.source / self.mapping[0]
        self.destination = self.destination / self.mapping[1]

        # Locate the appropriate binary
        system = platform.system().lower()
        self.build_binary = Path(__file__).parent / "binaries" / system / build_binaries[system]

    def patch_filename(self, filename: Path) -> str:
        if filename.parents[-2].name != self.mapping[0]:  # Not our problem
            return str(filename)
        
        return str(Path(os.sep.join([self.mapping[1]] + str(filename).split(os.sep)[1:])).with_suffix(self.destination_extension))
