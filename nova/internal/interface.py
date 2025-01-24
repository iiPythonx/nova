# Copyright (c) 2025 iiPython

# Modules
from typing import Optional
from collections import deque
from datetime import datetime

from rich.box import SIMPLE
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
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
        [table.add_column(column) for column in ["Time", "Event", "Message"]]
        for row in self.log_buffer:
            table.add_row(*row)

        return Panel(table, title = "Logs")

    def _render_change(
        self,
        path: Optional[str] = None,
        time: Optional[float] = None,
        reloads: Optional[list[str]] = None
    ) -> Panel:
        table = Table(show_edge = False, show_header = False, box = SIMPLE)
        table.add_row("File Path:", path or "N/A")
        table.add_row("Render Time:", f"{time}ms" if time is not None else "N/A")
        table.add_row("Reloaded:", " ".join(reloads) if reloads else "N/A")
        return Panel(table, title = "Last change", title_align = "left")

    def _render_general(self, reload: bool, connections: int) -> Panel:
        group = Group(
            f"Auto-reload is {'[green]enabled' if reload else '[red]disabled'}[/].",
            f"Serving {connections} active connections."
        )
        return Panel(group, title = f"Nova v{__version__}", title_align = "left")

    # Public methods
    def update_log(self, event: str, message: str) -> None:
        self.log_buffer.append((datetime.now().strftime("%H:%M:%S"), event, message))
        self._layout["bottom"].update(self._render_table())

    def update_last_change(self, *args) -> None:
        self._layout["right"].update(self._render_change(*args))

    def update_general(self, reload: bool, connections: int) -> None:
        self._layout["left"].update(self._render_general(reload, connections))
