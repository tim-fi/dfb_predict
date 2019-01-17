import tkinter as tk
import tkinter.ttk as ttk

from .base import Tab
from ..jobs import ThreadJob
from ..widgets import QueryList, SelectBox, ScrollableText, ScrollableList, RangePointSelectorWidget
from ...db import DB, RangeSelector, Match, Group, Season


__all__ = (
    "PredictionTab",
)


class PredictionTab(Tab, verbose_name="prediction"):
    """This tab contains all things related to making predictions."""
    def create_widgets(self):
        self._model_selection = SelectBox(self, ["---"], "Choose model:")
        self._model_selection.pack(fill=tk.X, expand=True)
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

        self._output_frame = OutputFrame(self)
        self._output_frame.pack(fill=tk.BOTH, expand=True)

        self.master.bind("<<NewModel>>", self._update_models, add="+")

    def _update_models(self, event):
        self._model_selection.set_options(self.master.models.keys())

    def _model_tracer(self, *args):
        self.event_generate("<<NewModelSelected>>")


class OutputFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._text = ScrollableText(self.master, height=1, width=40)
        self._text.pack(in_=self, fill=tk.BOTH, expand=True)
        self._text.lock_text()

        self.bind_all("<<NewText>>", self._update_text, add="+")

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

        self.bind_all("<<NewPrediction>>", self._update_jobs, add="+")

    def _update_jobs(self, event):
        self._job_list.set_values([f"{host_name} vs {guest_name} via {model}" for host_name, guest_name, model in self.master.master.prediction_jobs])

    def _prediction_job(self):
        self.master.master.text = ""
        results = []
        for host_name, guest_name, model in self.master.master.prediction_jobs:
            print(host_name, guest_name, model)
            model = self.master.master.models[model]
            try:
                results.append(model.make_prediction(host_name, guest_name))
            except Exception as e:
                self.master.text = e.args[0]
                return
        self.master.master.text = "\n".join([str(result) for result in results])
        self.master.master.prediction_jobs = []


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

        self._trigger = ttk.Button(self.master, text="queue prediction", command=ThreadJob(self._prediction_config_job))
        self._trigger.pack(in_=self, fill=tk.X, expand=True)

        self.bind_all("<<NewModelSelected>>", self._model_updated, add="+")

    def _model_updated(self, *args):
        model = self.master._model_selection.selection
        if model is not None:
            self._selector.copy(self.master.master.models[model].selector)
            self._host_team_list.fill()
            self._guest_team_list.fill()

    def _prediction_config_job(self):
        host = self._host_team_list.get_cur()
        guest = self._guest_team_list.get_cur()
        model = self.master._model_selection.selection

        if host is None or guest is None:
            tk.messagebox.showerror("Error", "Please select teams to make a prediction...")
        elif model is None:
            tk.messagebox.showerror("Error", "Please select a prediction method.")
        else:
            self.master.master.prediction_jobs.append((host[0], guest[0], model))


class QueuePopulateFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, text="...", **kwargs)
        self._direct_selection_frame = tk.Frame(self.master)
        self._direct_selection_frame.pack(in_=self, side=tk.RIGHT, fill=tk.X)

        self._direct_selector = RangePointSelectorWidget(self.master, text="Group from DB")
        self._direct_selector.pack(in_=self._direct_selection_frame, fill=tk.X)

        self._trigger = ttk.Button(self.master, text="add to queue", command=ThreadJob(self._direct_selection_job))
        self._trigger.pack(in_=self._direct_selection_frame, fill=tk.X)

        self.bind_all("<<NewModelSelected>>", self._model_updated, add="+")

    def _model_updated(self, *args):
        with DB.get_session() as session:
            selector = self.master.master.models[self.master._model_selection.selection].selector
            self._direct_selector.set_years([
                season.year
                for season in session.query(Season).filter(
                    Season.year >= selector.start.year,
                    Season.year <= selector.end.year
                )
            ])

    def _direct_selection_job(self):
        with DB.get_session() as session:
            selection = self._direct_selector.selection
            model = self.master._model_selection.selection
            self.master.master.prediction_jobs.extend((
                (match.host.name, match.guest.name, model)
                for match in session.query(Match).join(Match.group, Group.season).filter(
                    Group.order_id == selection.group,
                    Season.year == selection.year
                )
            ))
