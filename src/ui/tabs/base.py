import tkinter as tk
import tkinter.ttk as ttk


__all__ = (
    "Tab",
    "Tabs"
)


class Tab(tk.Frame):
    """Base tab class

    This class is "used" to "collect" all tabs, i.e.
    tabclasses, in a registry, thus making it easier
    to iterate over them programatically.
    """
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
        raise NotImplementedError()


class Tabs(ttk.Notebook):
    """Tab container

    This class is the widget which contains all the
    tabs from the tabclass registry.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for label, tab_class in Tab.registry.items():
            self.add(tab_class(self), text=label, compound=tk.TOP)
