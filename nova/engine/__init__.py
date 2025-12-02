# Copyright (c) 2025 iiPython

# Modules
import re
import time
import typing
import shutil
from pathlib import Path
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader

from nova.plugins import Plugin, LOAD_ORDER, fetch_plugin

# Initialization
RE_JINJA_EXTEND = re.compile(r"{% \w* [\"'](\w.+)[\"'][\w ]* %}")
RE_HTML_REFERENCE = re.compile(r"<(?:link|script).* (?:href|src) ?= ?[\"']([\w/.]+)[\"'].*>")
DEV_MODE_JS = "<script>(new WebSocket(`ws://${window.location.host}/_nova`)).addEventListener(\"message\",e=>{if(JSON.parse(e.data).includes(window.location.pathname))window.location.reload();});</script></body></html>"

# Handle engine
@dataclass
class EngineConfig:
    source: Path
    output: Path
    static: Path
    plugins: dict[str, Plugin]

@dataclass
class BuildInformation:
    time_taken: float
    plugin_time_taken: dict[str, float]
    dependencies: dict[Path, list[Path]]

class NovaEngine:
    def __init__(self, config: dict[str, typing.Any]) -> None:

        # Load in settings
        self.config = EngineConfig(
            Path(config["source"]).resolve(),
            Path(config["output"]).resolve(),
            (Path(config["source"]) / "static").resolve(),
            {}
        )

        for plugin in [{"type": "static"}, *config["plugins"]]:
            self.config.plugins[plugin["type"]] = fetch_plugin(plugin["type"])(self, plugin)  # type: ignore

        # Setup Jinja2 environment
        self.jinja2 = Environment(loader = FileSystemLoader(self.config.source))

    async def build(self, dev_mode: bool = False) -> BuildInformation:

        # Clean the old output location
        if self.config.output.is_dir():
            shutil.rmtree(self.config.output)

        # Process Jinja2 files
        start, dependencies = time.perf_counter(), {}
        for file in self.config.source.rglob("*"):
            if file.suffix not in [".jinja2", ".j2", ".html"] or file.is_relative_to(self.config.static):
                continue

            relative = file.relative_to(self.config.source)
            target_file = self.config.output / relative.with_suffix(".html")

            # Save resulting file
            result_html = self.jinja2.get_template(str(relative)).render(git_hash = "dsd")
            if not target_file.parent.is_dir():
                target_file.parent.mkdir(parents = True)

            target_file.write_text(result_html if not dev_mode else result_html.split("</body>")[0] + DEV_MODE_JS)

            # Track dependencies
            source_html = file.read_text()
            for dependency in RE_JINJA_EXTEND.findall(source_html) + RE_HTML_REFERENCE.findall(source_html):
                dependency = file.parent / dependency if dependency.startswith(".") else self.config.source / Path(dependency.lstrip("/"))
                dependencies[dependency] = (dependencies.get(dependency, [])) + [file]

        # Process plugins
        time_taken = {}
        for name, plugin in [(p, self.config.plugins[p]) for p in LOAD_ORDER if p in self.config.plugins]:
            start = time.perf_counter()
            plugin.build(dev_mode)
            time_taken[name] = time.perf_counter() - start

        return BuildInformation(
            time.perf_counter() - start,
            time_taken,
            dependencies
        )
