import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread, RLock

from .base import Tab
from ..widgets import ScrollableList, LabeledProgressbar
from ...db import DB
from ...acquisition import download_matches, clean_download_list


__all__ = (
    "DownloadTab",
)


class DownloadTab(Tab, verbose_name="download"):
    def create_widgets(self):
        self._download_frame = tk.Frame(self)
        self._download_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._year_list = ScrollableList(self, selectmode=tk.MULTIPLE)
        self._year_list.pack(in_=self._download_frame, fill=tk.BOTH, expand=True)

        self._download_button = ttk.Button(self, text="download", command=self._download)
        self._download_button.pack(in_=self._download_frame, fill=tk.X, expand=True)

        self._progressbar = LabeledProgressbar(self)
        self._progressbar.pack(in_=self._download_frame, fill=tk.X, expand=True)

        self._work_lock = RLock()
        self._current_year_selection = []
        self._populate_year_list()
        self._poll_list()

    def _populate_year_list(self):
        with DB.get_session() as session:
            years_to_download, _ = clean_download_list(session, range(2002, 2019))
        self._year_list.set_values([f"{year}/{(year % 100 + 1):0>2d}" for year in years_to_download])

    def _poll_list(self):
        now = self._year_list.curselection()
        if now != self._current_year_selection:
            self._progressbar.set_label(f"{len(now) * 306} matches selected  ")
            self._current_year_selection = now
        self.after(250, self._poll_list)

    def _download(self):
        if self._work_lock.acquire(blocking=False):
            t = Thread(target=self._download_job)
            t.start()
            self._work_lock.release()

    def _download_job(self):
        with self._work_lock:
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
                self._progressbar.set_label("populating model lists...")
                self._populate_year_list()
                self.master.prediction.fill_team_lists()
                self.master.prediction.fill_range_selector()
                self._progressbar.set_label("done")
            finally:
                self._progressbar.set_value(0)
