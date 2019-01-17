import tkinter as tk
import tkinter.ttk as ttk
from itertools import cycle

from .base import Tab
from ..data import AppData
from ..jobs import ThreadJob
from ..widgets import ScrollableList, LabeledProgressbar, SelectBox, RangeSelectorWidget
from ...prediction import Model
from ...db import DB
from ...acquisition import download_matches, clean_download_list


__all__ = (
    "DownloadTab",
)


class DownloadTab(Tab, verbose_name="download"):
    def create_widgets(self):
        self._model_frame = ModelFrame(self)
        self._model_frame.pack(in_=self, fill=tk.X)

        self._download_frame = DownloadFrame(self)
        self._download_frame.pack(in_=self, fill=tk.BOTH, expand=True)


class DownloadFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Download", **kwargs)
        self._year_list = ScrollableList(self, selectmode=tk.MULTIPLE)
        self._year_list.pack(fill=tk.BOTH, expand=True)

        self._download_button = ttk.Button(self, text="download", command=ThreadJob(self._download_job))
        self._download_button.pack(fill=tk.X)

        self._progressbar = LabeledProgressbar(self)
        self._progressbar.pack(fill=tk.X)

        self._current_year_selection = []

        self.bind_all("<<NewData>>", self._update_years, add="+")
        self.event_generate("<<NewData>>")
        self._poll_list()

    def _update_years(self, event):
        with DB.get_session() as session:
            years_to_download, _ = clean_download_list(session, range(2002, 2019))
        self._year_list.set_values([f"{year}/{(year % 100 + 1):0>2d}" for year in years_to_download])

    def _poll_list(self):
        now = self._year_list.curselection()
        if now != self._current_year_selection:
            self._progressbar.set_label(f"{len(now) * 306} matches selected  ")
            self._current_year_selection = now
        self.after(250, self._poll_list)

    def _download_job(self):
        selected_years = self._year_list.get_cur()
        if selected_years is None:
            tk.messagebox.showerror("Error", "Please select the years to download.")
            return
        selected_years = [int(year[:4]) for year in selected_years]

        try:
            with DB.get_session() as session:
                num_matches = len(selected_years) * 306
                progress_increment = 100 / num_matches

                self._progressbar.set_label("starting download...")
                for i, match in enumerate(download_matches(session, selected_years)):
                    session.add(match)
                    self._progressbar.step(progress_increment)
                    self._progressbar.set_label(f"{i + 1}/{num_matches}")

                self._progressbar.set_label("commiting changes...")
        except:  # noqa: E722
            self._progressbar.set_label("something went wrong...")
            raise
        else:
            self.event_generate("<<NewData>>")
            self._progressbar.set_label("done")
        finally:
            self._progressbar.set_value(0)


class ModelFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Model", **kwargs)

        self._range_selector_widget = RangeSelectorWidget(self.master, text="Daterange")
        self._range_selector_widget.pack(in_=self, fill=tk.X, expand=True)

        self._model_selectbox = SelectBox(self.master, choices=list(Model.registry.keys()), label="Choose prediction method")
        self._model_selectbox.pack(in_=self, fill=tk.X, expand=True)

        self._button_label = tk.StringVar()
        self._button_label.set("build model")

        self._training_button = ttk.Button(self.master, textvariable=self._button_label, command=ThreadJob(self._training_job))
        self._training_button.pack(in_=self, fill=tk.X, expand=True)

        self.master.bind_all("<<NewData>>", self._update_range, add="+")

    def _update_range(self, event):
        self._range_selector_widget.populate_years()

    def _training_job(self):
        done = False
        animation = iter(cycle([
            "|", "/", "-", "\\"
        ]))

        def _loading_animation():
            if not done:
                self._button_label.set(next(animation))
                self.after(100, _loading_animation)
            else:
                self._button_label.set("done")
                self.after(500, lambda: self._button_label.set("build model"))

        model_name = self._model_selectbox.selection
        selector = self._range_selector_widget.selection
        if model_name is None:
            tk.messagebox.showerror("Error", "Please select a model to train/calculate.")
        elif not selector.is_valid:
            tk.messagebox.showerror("Error", "Please make sure that your selection is sensible.")
        else:
            _loading_animation()
            with DB.get_session() as session:
                model = Model.registry[model_name](selector, session)
            setattr(model, "selector", selector)
            AppData.models[f"{model_name} ({str(selector)})"] = model
            done = True
