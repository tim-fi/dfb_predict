import tkinter as tk

from .base import Tab
from ..data import AppData
from ..widgets import ScrollableText, ScrollableList


__all__ = (
    "ResultsTab",
)


class ResultsTab(Tab, verbose_name="results"):
    """This tab contains all things related to viewing prediction results."""
    def create_widgets(self):
        self._output_frame = OutputFrame(self)
        self._output_frame.pack(fill=tk.BOTH)


class OutputFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._list = ScrollableList(self, width=250, height=350)
        self._list.pack(side=tk.LEFT, fill=tk.Y)

        self._selected = None

        self._text = ScrollableText(self, width=400, height=350)
        self._text.pack(side=tk.RIGHT, fill=tk.BOTH)
        self._text.lock_text()

        self.bind_all("<<APPDATA.Results>>", self._update_results, add="+")
        self._poll_list()

    def _poll_list(self):
        (now,) = self._list.get_cur() or (None,)
        if now is not None and now != self._selected:
            self._text.unlock_text()
            self._text.set_text(str(AppData.results.data[now]))
            self._text.lock_text()
            self._selected = now
        self.after(50, self._poll_list)

    def _update_results(self, *args):
        self._list.set_values(AppData.results.data.keys())
