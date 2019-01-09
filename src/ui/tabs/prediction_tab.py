import tkinter as tk
import tkinter.ttk as ttk

from .base import Tab
from ..jobs import ThreadJob
from ..widgets import QueryList, SelectBox, RangeSelectorWidget, ScrollableText, ScrollableList
from ...prediction import Predictor
from ...db import DB, RangeSelector


__all__ = (
    "PredictionTab",
)


class PredictionTab(Tab, verbose_name="prediction"):
    """This tab contains all things related to making predictions."""
    def create_widgets(self):
        self.models = {}
        self._num_of_models = len(self.models)
        self.text = ""
        self._hash_of_text = hash(self.text)
        self.prediction_jobs = []
        self._num_of_pjobs = len(self.prediction_jobs)

        self._control_frame = tk.Frame(self)
        self._control_frame.pack(fill=tk.BOTH, expand=True)

        self._control_division = tk.Frame(self)
        self._control_division.pack(in_=self._control_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._model_frame = ModelFrame(self)
        self._model_frame.pack(in_=self._control_division, fill=tk.X)

        self._prediction_config_frame = PredictionConfigFrame(self)
        self._prediction_config_frame.pack(in_=self._control_division, fill=tk.X)

        self._prediction_queue_frame = PredictionQueueFrame(self)
        self._prediction_queue_frame.pack(in_=self._control_frame, side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._output_frame = OutputFrame(self)
        self._output_frame.pack(fill=tk.BOTH, expand=True)

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


class OutputFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._text = ScrollableText(self.master, height=10, width=50)
        self._text.pack(in_=self, fill=tk.BOTH, expand=True)
        self._text.lock_text()

        self.master.bind("<<NewText>>", self._update_text, add="+")

    def _update_text(self, event):
        self._text.unlock_text()
        self._text.set_text(self.master.text)
        self._text.lock_text()


class PredictionQueueFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Prediction Queue", **kwargs)

        self._job_list = ScrollableList(self.master)
        self._job_list.pack(in_=self, fill=tk.BOTH, expand=True)

        self._trigger = ttk.Button(self.master, text="execute queue", command=ThreadJob(self._prediction_job))
        self._trigger.pack(in_=self, fill=tk.X)

        self.master.bind("<<NewPrediction>>", self._update_jobs, add="+")

    def _update_jobs(self, event):
        self._job_list.set_values([f"{host_name} vs {guest_name} via {model}" for host_name, guest_name, model in self.master.prediction_jobs])

    def _prediction_job(self):
        self.master.text = ""
        results = []
        for host_name, guest_name, model in self.master.prediction_jobs:
            model = self.master.models[model]
            try:
                results.append(model.make_prediction(host_name, guest_name))
            except Exception as e:
                self.master.text = e.args[0]
                return
        self.master.text = "\n".join([str(result) for result in results])
        self.master.prediction_jobs = []


class ModelFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Model", **kwargs)

        self._range_selector_widget = RangeSelectorWidget(self.master, text="Daterange")
        self._range_selector_widget.pack(in_=self, fill=tk.X, expand=True)

        self._predictor_selectbox = SelectBox(self.master, choices=list(Predictor.registry.keys()), label="Choose prediction method")
        self._predictor_selectbox.pack(in_=self, fill=tk.X, expand=True)

        self._training_button = ttk.Button(self.master, text="build model", command=ThreadJob(self._training_job))
        self._training_button.pack(in_=self, fill=tk.X, expand=True)

        self.master.bind_all("<<NewData>>", self._update_range, add="+")

    def _update_range(self, event):
        self._range_selector_widget.populate_years()

    def _training_job(self):
        predictor_name = self._predictor_selectbox.selection
        selector = self._range_selector_widget.selection
        if predictor_name is None:
            tk.messagebox.showerror("Error", "Please select a model to train/calculate.")
        elif not selector.is_valid:
            tk.messagebox.showerror("Error", "Please make sure that your selection is sensible.")
        else:
            model = Predictor.registry[predictor_name]()
            with DB.get_session() as session:
                model.calculate_model(selector, session)
            setattr(model, "selector", selector)
            self.master.models[f"{predictor_name} ({str(selector)})"] = model


class PredictionConfigFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Prediction", **kwargs)
        self._selector = RangeSelector()

        self._label_frame = tk.Frame(self.master)
        self._label_frame.pack(in_=self, fill=tk.BOTH, expand=True)

        self._host_team_label = ttk.Label(self.master, text="Host:")
        self._host_team_label.pack(in_=self._label_frame, fill=tk.X, expand=True, side=tk.LEFT)

        self._guest_team_label = ttk.Label(self.master, text="Guest:")
        self._guest_team_label.pack(in_=self._label_frame, fill=tk.X, expand=True, side=tk.RIGHT)

        self._team_frame = tk.Frame(self.master)
        self._team_frame.pack(in_=self, fill=tk.BOTH, expand=True)

        self._host_team_list = QueryList(self.master, lambda: self._selector.build_team_query(), selectmode=tk.SINGLE, target_field="name")
        self._host_team_list.pack(in_=self._team_frame, fill=tk.BOTH, expand=True, side=tk.LEFT)

        self._guest_team_list = QueryList(self.master, lambda: self._selector.build_team_query(), selectmode=tk.SINGLE, target_field="name")
        self._guest_team_list.pack(in_=self._team_frame, fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self._model_selection = SelectBox(self.master, ["---"], "Choose model:")
        self._model_selection.pack(in_=self, fill=tk.X, expand=True)
        self._model_selection.add_tracer(self._model_tracer)

        self._trigger = ttk.Button(self.master, text="queue prediction", command=ThreadJob(self._prediction_config_job))
        self._trigger.pack(in_=self, fill=tk.X, expand=True)

        self.master.bind("<<NewModel>>", self._update_models, add="+")

    def _update_models(self, event):
        self._model_selection.set_options(self.master.models.keys())

    def _model_tracer(self, *args):
        selected_model = self._model_selection.selection
        if not selected_model:
            self._selector = RangeSelector()
        else:
            self._selector = self.master.models[selected_model].selector
        self._host_team_list.fill()
        self._guest_team_list.fill()

    def _prediction_config_job(self):
        host_id = self._host_team_list.get_cur()
        guest_id = self._guest_team_list.get_cur()
        model = self._model_selection.selection

        if host_id is None or guest_id is None:
            tk.messagebox.showerror("Error", "Please select teams to make a prediction...")
        elif model is None:
            tk.messagebox.showerror("Error", "Please select a prediction method.")
        else:
            self.master.prediction_jobs.append((host_id[0], guest_id[0], model))
