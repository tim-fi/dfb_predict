__all__ = (
    "AppData",
)


class _AppData:
    def __init__(self):
        self.models = {}
        self._num_of_models = len(self.models)
        self.text = ""
        self._hash_of_text = hash(self.text)
        self.prediction_jobs = []
        self._num_of_pjobs = len(self.prediction_jobs)

    def gather_events(self):
        events = []
        if len(AppData.models) != AppData._num_of_models:
            events.append("<<NewModel>>")
            AppData._num_of_models = len(AppData.models)
        if hash(AppData.text) != AppData._hash_of_text:
            events.append("<<NewText>>")
            AppData._hash_of_text = hash(AppData.text)
        if len(AppData.prediction_jobs) != AppData._num_of_pjobs:
            events.append("<<NewPrediction>>")
            AppData._num_of_pjobs = len(AppData.prediction_jobs)
        return events


AppData = _AppData()
