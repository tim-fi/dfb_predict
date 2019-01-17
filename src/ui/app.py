import tkinter as tk

from .tabs import Tabs


class App(tk.Frame):
    """Main body of the UI application"""
    def __init__(self, parent):
        super().__init__(parent)
        parent.resizable(0, 0)
        parent.title("DFB Predict")
        self.pack()

        self.models = {}
        self._num_of_models = len(self.models)
        self.text = ""
        self._hash_of_text = hash(self.text)
        self.prediction_jobs = []
        self._num_of_pjobs = len(self.prediction_jobs)

        self._tabs = Tabs(self)
        self._tabs.pack(fill=tk.BOTH, expand=True)

        self._generate_events()

    def _generate_events(self):
        if len(self.models) != self._num_of_models:
            self.event_generate("<<NewModel>>")
            self._num_of_models = len(self.models)
        if hash(self.text) != self._hash_of_text:
            self.event_generate("<<NewText>>")
            self._hash_of_text = hash(self.text)
        if len(self.prediction_jobs) != self._num_of_pjobs:
            self.event_generate("<<NewPrediction>>")
            self._num_of_pjobs = len(self.prediction_jobs)
        self.after(50, self._generate_events)

    @classmethod
    def run_app(cls):
        root = tk.Tk()
        app = cls(root)
        app.mainloop()
