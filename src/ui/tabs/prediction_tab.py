import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread, RLock

from .base import Tab
from ..widgets import QueryList, SelectBox
from ...prediction import Predictor
from ...db import DB, Team, RangeSelector


__all__ = (
    "PredictionTab",
)


class PredictionTab(Tab, verbose_name="prediction"):
    def create_widgets(self):
        self._selector = RangeSelector()

        self._control_frame = tk.Frame(self)
        self._control_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self._team_select_label_frame = tk.Frame(self)
        self._team_select_label_frame.pack(in_=self._control_frame, fill=tk.BOTH, expand=True)

        self._host_team_label = ttk.Label(self, text="Host:")
        self._host_team_label.pack(in_=self._team_select_label_frame, fill=tk.X, expand=True, side=tk.LEFT)

        self._guest_team_label = ttk.Label(self, text="Guest:")
        self._guest_team_label.pack(in_=self._team_select_label_frame, fill=tk.X, expand=True, side=tk.RIGHT)

        self._team_select_frame = tk.Frame(self)
        self._team_select_frame.pack(in_=self._control_frame, fill=tk.BOTH, expand=True)

        self._host_team_list = QueryList(self, self._selector.build_team_query, selectmode=tk.SINGLE)
        self._host_team_list.pack(in_=self._team_select_frame, fill=tk.BOTH, expand=True, side=tk.LEFT)

        self._guest_team_list = QueryList(self, self._selector.build_team_query, selectmode=tk.SINGLE)
        self._guest_team_list.pack(in_=self._team_select_frame, fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self._predictor_selectbox = SelectBox(self, choices=list(Predictor.registry.keys()), label="Choose prediction method:")
        self._predictor_selectbox.pack(in_=self._control_frame, fill=tk.X, expand=True)

        self._prediction_trigger = ttk.Button(self, text="predict", command=self._make_prediction)
        self._prediction_trigger.pack(in_=self._control_frame, fill=tk.X, expand=True)

        self._predictors = {
            name: predictor_class()
            for name, predictor_class in Predictor.registry.items()
        }

        self._work_lock = RLock()

        self._result_frame = tk.Frame(self)
        self._result_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self._result_text = tk.Text(self, height=10, width=50)
        self._result_text.pack(in_=self._result_frame, fill=tk.BOTH, expand=True)
        self._result_text.config(state=tk.DISABLED)

    def fill_team_lists(self):
        self._host_team_list.fill()
        self._guest_team_list.fill()

    def _make_prediction(self):
        if self._work_lock.acquire(blocking=False):
            host_id = self._host_team_list.get_cur()[0]
            guest_id = self._guest_team_list.get_cur()[0]
            predictor = self._predictor_selectbox.selection

            if host_id is None or guest_id is None:
                tk.messagebox.showerror("Error", "Please select teams to make a prediction...")
            elif predictor is None:
                tk.messagebox.showerror("Error", "Please select a prediction method.")
            else:
                Thread(target=self._prediction_job, args=(host_id, guest_id, self._predictors[predictor])).start()

            self._work_lock.release()

    def _prediction_job(self, host_id, guest_id, predictor):
        with self._work_lock, DB.get_session() as session:
            predictor.calculate_model(self._selector, session)
            host_name = session.query(Team).filter_by(id=host_id).first().name
            guest_name = session.query(Team).filter_by(id=guest_id).first().name
            result = predictor.make_prediction(host_name, guest_name)
            self._result_text.config(state=tk.NORMAL)
            self._result_text.delete('1.0', tk.END)
            self._result_text.insert(tk.END, str(result))
            self._result_text.config(state=tk.DISABLED)


"""
Iterate through all matches (with rematches...):

for i, host in enumerate(teams):
    for guest in teams[i+1:]:
        print(f"Game [>] - {host} vs {guest}")
        print(f"Game [<] - {guest} vs {host}")
"""
