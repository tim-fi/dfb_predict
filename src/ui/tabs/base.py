import tkinter as tk
import tkinter.ttk as ttk


__all__ = (
    "Tab",
    "Tabs"
)


class Tab(tk.Frame):
    registry = dict()

    def __init_subclass__(cls, verbose_name=None):
        _name = verbose_name or cls.__name__
        if _name in Tab.registry:
            raise RuntimeError(f"Tab with verbose name {repr(_name)} already exists.")
        else:
            Tab.registry[_name] = cls

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        raise NotImplemented()


class Tabs(ttk.Notebook):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for label, tab_class in Tab.registry.items():
            setattr(self.master, label, tab_class(self.master))
            self.add(getattr(self.master, label), text=label, compound=tk.TOP)
