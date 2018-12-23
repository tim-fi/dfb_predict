import tkinter as tk


__all__ = (
    "SelectBox",
)


class SelectBox(tk.Frame):
    """Custom widget: dropdown selectbox"""
    def __init__(self, parent, choices, label=None, set_default=False):
        super().__init__(parent)
        self._selected_value = tk.StringVar(parent)
        self._choices = choices
        if set_default:
            self._selected_value.set(self._choices[0])
        self._popup_menu = tk.OptionMenu(parent, self._selected_value, *self._choices)
        self._popup_menu.pack(in_=self, side=tk.RIGHT, fill=tk.X)
        if label is not None:
            self._label = tk.Label(parent, text=label or "Choose")
            self._label.pack(in_=self, side=tk.LEFT, fill=tk.X)
        self._selection = None
        self._selected_value.trace("w", self._trace_value)
        self._trace_callbacks = []

    def _trace_value(self, *args):
        self._selection = self._selected_value.get()
        for callback in self._trace_callbacks:
            callback(*args)

    def add_tracer(self, callback):
        self._trace_callbacks.append(callback)

    @property
    def selection(self):
        return self._selection
