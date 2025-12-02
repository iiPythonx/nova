# Copyright (c) 2025 iiPython

# Modules
import traceback
from typing import Optional

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.padding import Padding
from rich.layout import Layout

from nova import __version__
from nova.engine import BuildInformation

# Initialization
class Interface:
    def __init__(self) -> None:
        pass

    # Internal update methods
    def _init(self) -> None:
        if hasattr(self, "_layout"):
            return

        self._layout = self._render_view()
        self._live = Live(self._layout)
        self._live.console.clear()
        self._live.start()

    def _render_view(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name = "top", size = 6),
            Layout(self._render_change(), name = "bottom")
        )
        return layout

    def _render_change(
        self,
        info: Optional[BuildInformation] = None,
        file: Optional[str] = None,
        error: Optional[Exception] = None,
        deps: Optional[list[str]] = None
    ) -> Panel:
        if error is not None:
            self._live.update(Panel(
                Padding("\n".join(traceback.format_exception(error, limit = -1)), (1, 1)),
                title = "Jinja2 Exception",
                title_align = "left",
                subtitle = "(c) 2024-2025 iiPython",
                subtitle_align = "right",
                border_style = "red"
            ))
            return Panel("")
            
        elif info and file and deps:
            content = Group(
                f"[bright_black]{file}",
                f"[bright_black]{'─' * len(file)}",
                f"[bright_black]  → Build Time: [bold]{info.time_taken * 1000:.2f}ms[/]",
                *[
                    f"[bright_black]  → Added latency ({name}): [bold]{time * 1000:.2f}ms[/]"
                    for name, time in info.plugin_time_taken.items()
                ],
                f"[bright_black]  → Dependencies: {', '.join(deps)}"
            )

        else:
            content = Group(
                "[yellow]No additional builds have been generated yet.",
                "[yellow][?] Save a file to automatically rebuild your project.",
            )

        return Panel(
            Padding(content, (1, 1)),
            title = "Latest Build",
            title_align = "left",
            subtitle = "(c) 2024-2025 iiPython",
            subtitle_align = "right",
            border_style = "cyan"
        )

    def _render_general(self, reload: bool, connections: int) -> Panel:
        group = Group(
            f"Auto-reload is [bold]{'[green]enabled' if reload else '[red]disabled'}[/][/].",
            f"Serving [bold]{connections}[/] active connection{'s' if not connections or connections > 1 else ''}."
        )
        return Panel(Padding(group, (1, 1)), title = f"Nova v{__version__}", title_align = "left", border_style = "cyan")

    # Public methods
    def update_last_change(self, *args, **kwargs) -> None:
        self._init()
        self._live.update(self._layout)
        self._layout["bottom"].update(self._render_change(*args, **kwargs))

    def update_general(self, reload: bool, connections: int) -> None:
        self._init()
        self._layout["top"].update(self._render_general(reload, connections))
