from collections import OrderedDict

from .scrollable_list import ScrollableList
from ...db import DB


__all__ = (
    "QueryList",
)


class QueryList(ScrollableList):
    """Custom widget: listbox with autofill by db query"""
    def __init__(self, parent, query, selectmode=None, target_field=None):
        super().__init__(parent, selectmode=selectmode)
        self._query = query
        self._data = {}
        self._target_field = target_field or "id"
        self.fill()

    def fill(self):
        with DB.get_session() as session:
            self._data = OrderedDict([
                (str(instance), getattr(instance, self._target_field))
                for instance in (self._query() if callable(self._query) else self._query).with_session(session)
            ])
        self.set_values(self._data.keys())

    def get_cur(self):
        selection = super().get_cur()
        if selection is None:
            return None
        else:
            return [self._data[s] for s in selection]
