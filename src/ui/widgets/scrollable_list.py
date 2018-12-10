import tkinter as tk


__all__ = (
    "ScrollableList",
)


class ScrollableList(tk.Frame):
    def __init__(self, parent, selectmode=None):
        super().__init__(parent)
        self._scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL)
        self._list = tk.Listbox(parent, selectmode=selectmode or tk.SINGLE, yscrollcommand=self._scrollbar.set, exportselection=0)
        self._list.pack(in_=self, side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.config(command=self._adjust_listbox_view)
        self._scrollbar.pack(in_=self, side=tk.RIGHT, fill=tk.Y)

    def _adjust_listbox_view(self, *args):
        self._list.yview(*args)

    def pack(self, *args, **kwargs):
        super().pack(*args, **{**kwargs, "padx": 0, "pady": 0})

    def insert(self, index, *elements):
        self._list.insert(index, *elements)

    def delete(self, start, end):
        self._list.delete(start, end)

    def get(self, *indecies):
        if len(indecies) == 0:
            return None
        vals = [self._list.get(i) for i in indecies]
        return vals

    def curselection(self):
        return self._list.curselection()

    def get_cur(self):
        selection = self.curselection()
        if selection:
            return self.get(*selection)
        else:
            return None
