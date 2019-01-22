import tkinter as tk
import tkinter.ttk as ttk
from itertools import cycle
from multiprocessing import Process, Pipe
from time import sleep

from .base import Tab
from ..data import AppData
from ..jobs import ThreadJob
from ..widgets import ScrollableList, LabeledProgressbar, SelectBox, RangeSelectorWidget
from ...prediction import Model
from ...db import DB
from ...acquisition import download_matches, clean_download_list


__all__ = (
    "DataTab",
)


class DataTab(Tab, verbose_name="data"):
    """This tab contains all things related to the data/models used for predictions."""
    def create_widgets(self):
        self._model_frame = ttk.LabelFrame(self, text="Models")
        self._model_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._model_create_frame = ModelCreateFrame(self)
        self._model_create_frame.pack(in_=self._model_frame, fill=tk.X, expand=True)

        self._model_manage_frame = ModelManageFrame(self)
        self._model_manage_frame.pack(in_=self._model_frame, fill=tk.BOTH, expand=True)

        self._download_frame = DownloadFrame(self)
        self._download_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


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

        self.bind_all("<<DATA.YearsChanged>>", self._update_years, add="+")
        self.event_generate("<<DATA.YearsChanged>>")
        self._poll_list()

    def _update_years(self, event):
        with DB.get_session() as session:
            years_to_download, _ = clean_download_list(session, range(2003, 2019))
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
            self.event_generate("<<DATA.YearsChanged>>")
            self._progressbar.set_label("done")
        finally:
            self._progressbar.set_value(0)


class ModelCreateFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Create", **kwargs)

        self._range_selector_widget = RangeSelectorWidget(self, text="Daterange")
        self._range_selector_widget.pack(fill=tk.X)

        self._model_selectbox = SelectBox(self, choices=list(Model.registry.keys()), label="Choose prediction method")
        self._model_selectbox.pack(fill=tk.X)

        self._button_label = tk.StringVar()
        self._button_label.set("build model")

        self._training_button = ttk.Button(self, textvariable=self._button_label, command=ThreadJob(self._training_job))
        self._training_button.pack(fill=tk.X)

        self.bind_all("<<DATA.YearsChanged>>", self._update_range, add="+")

    def _update_range(self, event):
        self._range_selector_widget.populate_years()

    def _training_job(self):
        def process_job(p: Pipe, model_class, selector):
            with DB.get_session() as session:
                p.send(model_class(selector, session))
            p.close()

        model_name = self._model_selectbox.selection
        selector = self._range_selector_widget.selection
        if model_name is None:
            tk.messagebox.showerror("Error", "Please select a model to train/calculate.")
        elif not selector.is_valid:
            tk.messagebox.showerror("Error", "Please make sure that your selection is sensible.")
        else:
            p_out, p_in = Pipe(duplex=False)
            p = Process(target=process_job, args=(p_in, Model.registry[model_name], selector))
            p.start()
            animation = iter(cycle(["|", "/", "-", "\\"]))
            while not p_out.poll():
                self._button_label.set(next(animation))
                sleep(0.1)
            AppData.models.data[f"{model_name} ({str(selector)})"] = p_out.recv()
            p.join()
            self._button_label.set("done")
            self.after(500, lambda: self._button_label.set("build model"))


class ModelManageFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Manage", **kwargs)

        self._model_list = ScrollableList(self, selectmode=tk.MULTIPLE, height=150)
        self._model_list.pack(fill=tk.BOTH, expand=True)

        self._button_frame = tk.Frame(self)
        self._button_frame.pack(fill=tk.X, expand=True)

        self._delete_button = ttk.Button(self, text="delete", command=self._delete_models)
        self._delete_button.pack(in_=self._button_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._file_button_frame = tk.Frame(self)
        self._file_button_frame.pack(in_=self._button_frame, side=tk.RIGHT, fill=tk.X)

        self._load_button = ttk.Button(self, text="load", command=self._load_models)
        self._load_button.pack(in_=self._file_button_frame, side=tk.LEFT, fill=tk.X, expand=True)

        self._save_button = ttk.Button(self, text="save", command=self._save_models)
        self._save_button.pack(in_=self._file_button_frame, side=tk.RIGHT, fill=tk.X, expand=True)

        self.bind_all("<<APPDATA.Models>>", self._models_updated, add="+")

    def _models_updated(self, *args):
        self._model_list.set_values(AppData.models.data.keys())

    def _delete_models(self, *args):
        selected_models = self._model_list.get_cur()
        if selected_models is None:
            tk.messagebox.showerror("Error", "Can't delete nothing...")
        else:
            for model in selected_models:
                del AppData.models.data[model]

    def _load_models(self, *args):
        print("LOAD MODELS")

    def _save_models(self, *args):
        print("SAVE MODELS")
