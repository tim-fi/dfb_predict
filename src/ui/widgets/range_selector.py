import tkinter as tk
import tkinter.ttk as ttk

from .range_point_selector import RangePointSelectorWidget
from .select_box import SelectBox
from ...db.selectors import RangeSelector, RangePoint
from ...db import DB
from ...db.models import Season


__all__ = (
    "RangeSelectorWidget",
)


class RangeSelectorWidget(tk.Frame):
    """Custom Widget: A combination of inputs to generate a RangeSelector"""
    def __init__(self, *args, text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = tk.Label(self, text=text or "range")
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._input_frame = tk.Frame(self)
        self._input_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self._start = RangePointSelectorWidget(self, text="from")
        self._start.pack(in_=self._input_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._end = RangePointSelectorWidget(self, text="until")
        self._end.pack(in_=self._input_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self.add_tracer(self._tracer)
        self.populate_years()
        self.populate_groups()

        self._range_selection = RangeSelector()

    def add_tracer(self, tracer):
        self._start.add_tracer(tracer)
        self._end.add_tracer(tracer)

    def _tracer(self, *args):
        try:
            self._range_selection = RangeSelector(
                start=self._start.selection,
                end=self._end.selection
            )
        except TypeError as e:
            tk.messagebox.showerror("Error", e.args[0])

    def populate_years(self):
        self._start.populate_years()
        self._end.populate_years()

    def populate_groups(self):
        self._start.populate_groups()
        self._end.populate_groups()

    @property
    def selection(self):
        return self._range_selection
