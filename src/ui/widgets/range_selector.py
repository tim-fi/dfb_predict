import tkinter as tk
import tkinter.ttk as ttk

from .select_box import SelectBox
from ...db.selectors import RangeSelector, RangePoint


__all__ = (
    "RangeSelectorWidget",
)


class RangeSelectorWidget(tk.Frame):
    def __init__(self, *args, text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._outer_frame = tk.Frame(self)
        self._outer_frame.pack(fill=tk.X, expand=True)

        self._label = tk.Label(self, text=text or "range")
        self._label.pack(in_=self._outer_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._inner_frame = tk.Frame(self)
        self._inner_frame.pack(in_=self._outer_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self._start_frame = ttk.LabelFrame(self, text="von")
        self._start_frame.pack(in_=self._inner_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._start_year = SelectBox(self, ["----", *map(str, range(2002, 2018))], set_default=True)
        self._start_year.pack(in_=self._start_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._start_group = SelectBox(self, ["--", *map(str, range(1, 35))], set_default=True)
        self._start_group.pack(in_=self._start_frame, side=tk.RIGHT, fill=tk.X, expand=True)
    
        self._end_frame = ttk.LabelFrame(self, text="bis")
        self._end_frame.pack(in_=self._inner_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self._end_year = SelectBox(self, ["----", *map(str, range(2002, 2018))], set_default=True)
        self._end_year.pack(in_=self._end_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._end_group = SelectBox(self, ["--", *map(str, range(1, 35))], set_default=True)
        self._end_group.pack(in_=self._end_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self.add_tracer(self._tracer)

        self._range_selection = RangeSelector()

    def add_tracer(self, tracer):
        self._start_year.add_tracer(tracer)
        self._start_group.add_tracer(tracer)
        self._end_year.add_tracer(tracer)
        self._end_group.add_tracer(tracer)

    @property
    def start_year_selection(self):
        selection = self._start_year.selection
        if selection is None or selection == "----":
            return None
        else:
            return int(selection)

    @property
    def end_year_selection(self):
        selection = self._end_year.selection
        if selection is None or selection == "----":
            return None
        else:
            return int(selection)

    @property
    def start_group_selection(self):
        selection = self._start_group.selection
        if selection is None or selection == "--":
            return None
        else:
            return int(selection)

    @property
    def end_group_selection(self):
        selection = self._end_group.selection
        if selection is None or selection == "--":
            return None
        else:
            return int(selection)

    def _tracer(self, *args):
        try:
            self._range_selection = RangeSelector(
                start=RangePoint(
                    year=self.start_year_selection,
                    group=self.start_group_selection
                ),
                end=RangePoint(
                    year=self.end_year_selection,
                    group=self.end_group_selection
                )
            )
        except TypeError as e:
            tk.messagebox.showerror("Error", e.args[0])

    @property
    def selection(self):
        return self._range_selection
