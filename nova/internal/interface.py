# Copyright (c) 2025 iiPython
# Design inspired by https://github.com/Lysagxra/BunkrDownloader.

# Modules
from typing import Optional
from collections import deque
from datetime import datetime

from rich.box import SIMPLE
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.padding import Padding
from rich.layout import Layout

from nova import __version__

# Initialization
class Interface:
    def __init__(self) -> None:
        self.log_buffer = deque(maxlen = 5)

        # Start the live
        self._layout = self._render_view()
        self._live = Live(self._layout)
        self._live.console.clear()
        self._live.start()

    # Internal update methods
    def _render_view(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name = "top"),
            Layout(self._render_table(), name = "bottom")
        )
        layout["top"].split_row(
            Layout("", name = "left"),
            Layout(self._render_change(), name = "right")
        )
        return layout

    def _render_table(self) -> Panel:
        table = Table(show_edge = False, box = SIMPLE)  
        table.add_column("[light_cyan3]Time", style = "pale_turquoise4", width = 15)
        table.add_column("[light_cyan3]Event", style = "pale_turquoise4", width = 20)
        table.add_column("[light_cyan3]Message", style = "pale_turquoise4")
        for row in self.log_buffer:
            table.add_row(*row)

        return Panel(
            Padding(table, (1, 1)),
            title = "Logs",
            title_align = "left",
            subtitle = "(c) 2024-2025 iiPython",
            subtitle_align = "right",
            border_style = "cyan"
        )

    def _render_change(
        self,
        path: Optional[str] = None,
        time: Optional[float] = None,
        reloads: Optional[list[str]] = None,
        src: Optional[str] = None,
        dist: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> Panel:
        if error is not None:
            content = Group(
                "[red underline]Jinja2 Exception[/]",
                str(error)
            )

        elif path is None:
            content = "[red]Nothing has been generated yet.[/]"

        else:
            content = Group(
                f"[light_cyan3]{path}",
                f"[light_cyan3]  → Render Time: {time}ms",
                f"[light_cyan3]  → Reloaded: {' '.join(reloads or [])}",
                f"\n[light_cyan3]Looking for changes in [yellow underline]{src}[/], writing to [purple underline]{dist}[/]."
            )

        return Panel(Padding(content, (1, 1)), title = "Last change", title_align = "left", border_style = "cyan")

    def _render_general(self, reload: bool, connections: int) -> Panel:
        group = Group(
            f"Auto-reload is {'[green]enabled' if reload else '[red]disabled'}[/].",
            f"Serving {connections} active connection{'s' if not connections or connections > 1 else ''}."
        )
        return Panel(Padding(group, (1, 1)), title = f"Nova v{__version__}", title_align = "left", border_style = "cyan")

    # Public methods
    def update_log(self, event: str, message: str) -> None:
        self.log_buffer.append((datetime.now().strftime("%H:%M:%S"), event, message))
        self._layout["bottom"].update(self._render_table())

    def update_last_change(self, *args, **kwargs) -> None:
        self._layout["right"].update(self._render_change(*args, **kwargs))

    def update_general(self, reload: bool, connections: int) -> None:
        self._layout["left"].update(self._render_general(reload, connections))
