import tkinter as tk
from collections import OrderedDict

from .scrollable_list import ScrollableList
from ...db import DB


__all__ = (
    "QueryList",
)


class QueryList(ScrollableList):
    """Custom widget: listbox with autofill by db query"""
    def __init__(self, parent, query, selectmode=None):
        super().__init__(parent, selectmode=selectmode)
        self._query = query
        self._data = {}
        self.fill()

    def fill(self):
        with DB.get_session() as session:
            self._data = OrderedDict([
                (str(instance), instance.id)
                for instance in (self._query() if callable(self._query) else self._query).with_session(session)
            ])
        self.set_values(self._data.keys())

    def get_cur(self):
        selection = super().get_cur()
        if selection is None:
            return None
        else:
            return [self._data[s] for s in selection]
