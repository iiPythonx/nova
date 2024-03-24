# Copyright (c) 2024 iiPython

# Modules
import subprocess
from shutil import which
from types import FunctionType
from importlib import import_module

from rich.console import Console

# Handle plugin initialization
def plugin_load_callback(name: str, class_name: str) -> FunctionType:
    def load_plugin() -> None:
        return getattr(import_module(name, "nova.plugins"), class_name)

    return load_plugin

available_plugins = {
    "sass": {
        "module": plugin_load_callback(".plugin_sass", "SassPlugin")
    },
    "static": {
        "module": plugin_load_callback(".plugin_static", "StaticPlugin")
    },
    # "autowebp": {
    #     "module": plugin_load_callback(".plugin_autowebp", "AutoWebpPlugin"),
    #     "requirements": ["pillow", "beautifulsoup4"]
    # }
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
