import tkinter as tk


__all__ = (
    "ScrollableText",
)


class ScrollableText(tk.Frame):
    """Custom widget: listbox with scrollbar"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = tk.Text(self)
        self._scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self._text.yview)
        self._text["yscrollcommand"] = self._scrollbar.set

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.pack_propagate(0)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def lock_text(self):
        self._text.config(state=tk.DISABLED)

    def unlock_text(self):
        self._text.config(state=tk.NORMAL)

    def clear_text(self):
        self._text.delete('1.0', tk.END)

    def add_text(self, text):
        self._text.insert(tk.END, str(text))

    def set_text(self, text):
        self.clear_text()
        self.add_text(text)
