import tkinter as tk

from .tabs import Tabs
from .data import AppData


class App(tk.Frame):
    """Main body of the UI application"""
    def __init__(self, parent):
        super().__init__(parent)
        parent.resizable(0, 0)
        parent.title("DFB Predict")
        self.pack()

        self._tabs = Tabs(self)
        self._tabs.pack()

        self.after(50, self._generate_events)

    def _generate_events(self):
        for event in AppData.gather_events():
            self.event_generate(event)
        self.after(50, self._generate_events)

    @classmethod
    def run_app(cls):
        root = tk.Tk()
        app = cls(root)
        app.mainloop()
