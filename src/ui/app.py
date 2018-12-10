import tkinter as tk


class App(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        parent.resizable(0, 0)
        parent.title("DFB Predict")
        self.pack()

    @classmethod
    def run_app(cls):
        root = tk.Tk()
        app = cls(root)
        app.mainloop()
