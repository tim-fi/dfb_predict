import tkinter as tk
import tkinter.ttk as ttk

from .select_box import SelectBox
from ...db.selectors import RangeSelector, RangePoint
from ...db import DB
from ...db.models import Season


__all__ = (
    "RangePointSelectorWidget",
)


class RangePointSelectorWidget(ttk.LabelFrame):
    """Custom Widget: A combination of inputs to generate a RangeSelector"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._year = SelectBox(self, choices=["----"], set_default=True)
        self._year.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._group = SelectBox(self, choices=["--"], set_default=True)
        self._group.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self.add_tracer(self._tracer)
        self.populate_years()
        self.populate_groups()

        self._range_selection = RangeSelector()

    def add_tracer(self, tracer):
        self._year.add_tracer(tracer)
        self._group.add_tracer(tracer)

    @property
    def year_selection(self):
        return self._clean_selection(self._year.selection)

    @property
    def group_selection(self):
        return self._clean_selection(self._group.selection)

    @staticmethod
    def _clean_selection(selection):
        try:
            return int(selection)
        except (ValueError, TypeError):
            return None

    def _tracer(self, *args):
        try:
            self._selection = RangePoint(
                year=self.year_selection,
                group=self.group_selection
            )
        except TypeError as e:
            tk.messagebox.showerror("Error", e.args[0])

    def populate_years(self):
        with DB.get_session() as session:
            self.set_years([year for (year,) in session.query(Season.year).all()])

    def populate_groups(self):
        self._group.set_options(["--", *map(str, range(1, 35))], set_val="--")

    def set_years(self, years):
        years.sort()
        self._year.set_options(["----", *years], set_val="----")

    @property
    def selection(self):
        return self._selection
