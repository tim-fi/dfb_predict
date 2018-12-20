import tkinter as tk

from .tabs import Tabs


class App(tk.Frame):
    """Main body of the UI application"""
    def __init__(self, parent):
        super().__init__(parent)
        parent.resizable(0, 0)
        parent.title("DFB Predict")
        self.pack()

        self._tabs = Tabs(parent)
        self._tabs.pack(fill=tk.BOTH, expand=True)

    @classmethod
    def run_app(cls):
        root = tk.Tk()
        app = cls(root)
        app.mainloop()
