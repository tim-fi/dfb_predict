import tkinter as tk
import tkinter.ttk as ttk

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

        self._start_frame = ttk.LabelFrame(self, text="from")
        self._start_frame.pack(in_=self._input_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._start_year = SelectBox(self, ["----"], set_default=True)
        self._start_year.pack(in_=self._start_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._start_group = SelectBox(self, ["--"], set_default=True)
        self._start_group.pack(in_=self._start_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self._end_frame = ttk.LabelFrame(self, text="until")
        self._end_frame.pack(in_=self._input_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self._end_year = SelectBox(self, ["----"], set_default=True)
        self._end_year.pack(in_=self._end_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._end_group = SelectBox(self, ["--"], set_default=True)
        self._end_group.pack(in_=self._end_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self.add_tracer(self._tracer)
        self.populate_years()
        self.populate_groups()

        self._range_selection = RangeSelector()

    def add_tracer(self, tracer):
        self._start_year.add_tracer(tracer)
        self._start_group.add_tracer(tracer)
        self._end_year.add_tracer(tracer)
        self._end_group.add_tracer(tracer)

    @property
    def start_year_selection(self):
        return self._clean_selection(self._start_year.selection)

    @property
    def end_year_selection(self):
        return self._clean_selection(self._end_year.selection)

    @property
    def start_group_selection(self):
        return self._clean_selection(self._start_group.selection)

    @property
    def end_group_selection(self):
        return self._clean_selection(self._end_group.selection)

    @staticmethod
    def _clean_selection(selection):
        try:
            return int(selection)
        except (ValueError, TypeError):
            return None

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

    def populate_years(self):
        with DB.get_session() as session:
            years = [year for (year,) in session.query(Season.year).all()]
            years.sort()
            self._start_year.set_options(["----", *years], set_val="----")
            self._end_year.set_options(["----", *years], set_val="----")

    def populate_groups(self):
        self._start_group.set_options(["--", *map(str, range(1, 35))])
        self._end_group.set_options(["--", *map(str, range(1, 35))])

    @property
    def selection(self):
        return self._range_selection
