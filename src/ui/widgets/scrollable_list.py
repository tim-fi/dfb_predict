import tkinter as tk


__all__ = (
    "ScrollableList",
)


class ScrollableList(tk.Frame):
    """Custom widget: listbox with scrollbar"""
    def __init__(self, *args, selectmode=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._list = tk.Listbox(self, selectmode=selectmode or tk.SINGLE, exportselection=0)
        self._scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self._list.yview)
        self._list["yscrollcommand"] = self._scrollbar.set

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.pack_propagate(0)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def set_values(self, elements):
        self.clear()
        self.extend(*elements)

    def extend(self, *elements):
        for element in elements:
            self.append(element)

    def append(self, element):
        self.insert(tk.END, element)

    def clear(self):
        self.delete(0, tk.END)

    def insert(self, index, *elements):
        self._list.insert(index, *elements)

    def delete(self, start, end):
        self._list.delete(start, end)

    def get(self, *indecies):
        if len(indecies) == 0:
            return None
        return [self._list.get(i) for i in indecies]

    def curselection(self):
        return self._list.curselection()

    def get_cur(self):
        selection = self.curselection()
        if selection:
            return self.get(*selection)
        else:
            return None
