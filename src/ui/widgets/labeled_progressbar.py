import tkinter as tk
import tkinter.ttk as ttk


__all__ = (
    "LabeledProgressbar",
)


class LabeledProgressbar(tk.Frame):
    """Custom widget: progressbar with label on it"""
    def __init__(self, *args, length=None, mode=None, orient=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._style = ttk.Style(self)
        self._style.layout(
            "LabeledProgressbar",
            [
                (
                    'Horizontal.Progressbar.trough',
                    {
                        'children': [
                            (
                                'Horizontal.Progressbar.pbar',
                                {'side': 'left', 'sticky': 'ns'}
                            )
                        ],
                        'sticky': 'nswe'
                    }
                ),
                (
                    'Horizontal.Progressbar.label',
                    {'sticky': ''}
                )
            ]
        )

        self._progress = ttk.Progressbar(self, length=length or 100, mode=mode or "determinate", orient=orient or "horizontal", style="LabeledProgressbar")
        self._progress.pack(fill=tk.X)

    def set_label(self, label):
        self._style.configure("LabeledProgressbar", text=label)

    def set_value(self, val):
        self._progress["value"] = val

    def start(self, *args, **kwargs):
        self._progress.start(*args, **kwargs)

    def stop(self, *args, **kwargs):
        self._progress.stop(*args, **kwargs)

    def step(self, *args, **kwargs):
        self._progress.step(*args, **kwargs)
