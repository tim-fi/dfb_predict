import tkinter as tk
import tkinter.ttk as ttk

from .base import Tab
from ..data import AppData
from ..jobs import ThreadJob
from ..widgets import SelectBox, ScrollableList, RangePointSelectorWidget
from ...db import DB, RangeSelector, Match, Group, Season


__all__ = (
    "PredictionTab",
)


class PredictionTab(Tab, verbose_name="prediction"):
    """This tab contains all things related to making predictions."""
    def create_widgets(self):
        self._model_selection = SelectBox(self, choices=["---"], label="Choose model:")
        self._model_selection.pack(fill=tk.X)
        self._model_selection.add_tracer(self._model_tracer)

        self._control_frame = tk.Frame(self)
        self._control_frame.pack(fill=tk.BOTH, expand=True)

        self._control_division = tk.Frame(self)
        self._control_division.pack(in_=self._control_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._prediction_config_frame = PredictionConfigFrame(self)
        self._prediction_config_frame.pack(in_=self._control_division, fill=tk.X)

        self._queue_populate_frame = QueuePopulateFrame(self)
        self._queue_populate_frame.pack(in_=self._control_division, fill=tk.X)

        self._prediction_queue_frame = PredictionQueueFrame(self)
        self._prediction_queue_frame.pack(in_=self._control_frame, side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.bind_all("<<APPDATA.Models>>", self._update_models, add="+")

    def _update_models(self, event):
        self._model_selection.set_options(AppData.models.data.keys())

    def _model_tracer(self, *args):
        self.event_generate("<<PREDICTION.NewModelSelected>>")


class PredictionQueueFrame(ttk.LabelFrame):
    """This frame contains all things related to prediction queue."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Prediction Queue", **kwargs)

        self._job_list = ScrollableList(self)
        self._job_list.pack(fill=tk.BOTH, expand=True)

        self._trigger = ttk.Button(self, text="execute queue", command=ThreadJob(self._prediction_job))
        self._trigger.pack(fill=tk.X)

        self.bind_all("<<APPDATA.PredictionJobs>>", self._update_jobs, add="+")

    def _update_jobs(self, event):
        self._job_list.set_values([f"{host_name} vs {guest_name} via {model}" for host_name, guest_name, model in AppData.prediction_jobs.data])

    def _prediction_job(self):
        for host_name, guest_name, _model in AppData.prediction_jobs.data:
            model = AppData.models.data[_model]
            try:
                AppData.results.data[f"{host_name} vs {guest_name} via {_model}"] = model.make_prediction(host_name, guest_name)
            except Exception as e:
                tk.messagebox.showerror("Error", str(e))
                return
        tk.messagebox.showinfo("Done", "Check the 'results'-tab for the results.")
        AppData.prediction_jobs.data = []


class PredictionConfigFrame(ttk.LabelFrame):
    """This tab contains all things related to making single predictions."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="Prediction", **kwargs)
        self._selector = RangeSelector()

        self._label_frame = tk.Frame(self)
        self._label_frame.pack(fill=tk.BOTH, expand=True)

        self._host_team_label = ttk.Label(self, text="Host:")
        self._host_team_label.pack(in_=self._label_frame, fill=tk.X, expand=True, side=tk.LEFT)

        self._guest_team_label = ttk.Label(self, text="Guest:")
        self._guest_team_label.pack(in_=self._label_frame, fill=tk.X, expand=True, side=tk.RIGHT)

        self._team_frame = tk.Frame(self)
        self._team_frame.pack(fill=tk.BOTH, expand=True)

        self._host_team_list = ScrollableList(self, selectmode=tk.SINGLE, height=150)
        self._host_team_list.pack(in_=self._team_frame, fill=tk.BOTH, expand=True, side=tk.LEFT)

        self._guest_team_list = ScrollableList(self, selectmode=tk.SINGLE, height=150)
        self._guest_team_list.pack(in_=self._team_frame, fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self._trigger = ttk.Button(self, text="queue prediction", command=ThreadJob(self._prediction_config_job))
        self._trigger.pack(fill=tk.X, expand=True)

        self.bind_all("<<PREDICTION.NewModelSelected>>", self._model_updated, add="+")

    def _model_updated(self, *args):
        model = self.master._model_selection.selection
        if model is not None and model in AppData.models.data:
            model = AppData.models.data[model]
            self._selector.copy(model.selector)
            self._host_team_list.set_values(model.teams)
            self._guest_team_list.set_values(model.teams)

    def _prediction_config_job(self):
        host = self._host_team_list.get_cur()
        guest = self._guest_team_list.get_cur()
        model = self.master._model_selection.selection

        if not model:
            tk.messagebox.showerror("Error", "Please select a model to make the predictions with.")
        elif host is None or guest is None:
            tk.messagebox.showerror("Error", "Please select teams to make a prediction.")
        else:
            AppData.prediction_jobs.data.append((host[0], guest[0], model))


class QueuePopulateFrame(ttk.LabelFrame):
    """This tab contains all things related to filling the prediction queue from external data."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="...", **kwargs)
        self._direct_selection_frame = tk.Frame(self)
        self._direct_selection_frame.pack(side=tk.RIGHT, fill=tk.X)

        self._direct_selector = RangePointSelectorWidget(self, text="Group from DB")
        self._direct_selector.pack(in_=self._direct_selection_frame, fill=tk.X)

        self._trigger = ttk.Button(self, text="add to queue", command=ThreadJob(self._direct_selection_job))
        self._trigger.pack(in_=self._direct_selection_frame, fill=tk.X)

        self.bind_all("<<PREDICTION.NewModelSelected>>", self._model_updated, add="+")

    def _model_updated(self, *args):
        with DB.get_session() as session:
            model = self.master._model_selection.selection
            if model is not None and model in AppData.models.data:
                selector = AppData.models.data[model].selector
                self._direct_selector.set_years([
                    season.year
                    for season in session.query(Season).filter(selector.build_filters(ignore_groups=True))
                ])

    def _direct_selection_job(self):
        with DB.get_session() as session:
            selection = self._direct_selector.selection
            model = self.master._model_selection.selection

            if not model:
                tk.messagebox.showerror("Error", "Please select a model to make the predictions with.")
            elif selection.is_null() or selection.is_partial():
                tk.messagebox.showerror("Error", "Please select a proper group to predict.")
            else:
                AppData.prediction_jobs.data.extend((
                    (match.host.shortname, match.guest.shortname, model)
                    for match in session.query(Match).join(Match.group, Group.season).filter(
                        Group.order_id == selection.group,
                        Season.year == selection.year
                    )
                ))
