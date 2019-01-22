from dataclasses import dataclass, field, fields
from typing import Dict, List, Tuple, Generic, TypeVar, Callable, Optional

from ..prediction import Model, PredictionResult

__all__ = (
    "AppData",
)


T = TypeVar('T')
K = TypeVar('K')
PredictionJob = Tuple[str, str, str]


@dataclass
class _AppDataField(Generic[T, K]):
    event: str
    data: T
    _check_func: Callable[[T], K]
    _check_val: Optional[K] = field(init=False, default=None)

    @property
    def changed(self):
        check = self._check_func(self.data)
        if check != self._check_val:
            self._check_val = check
            return True
        else:
            return False


@dataclass
class _AppData:
    models: _AppDataField[Dict[str, Model], int] =\
        field(init=False, default_factory=lambda: _AppDataField("<<APPDATA.Models>>", {}, len))
    results: _AppDataField[Dict[str, PredictionResult], int] =\
        field(init=False, default_factory=lambda: _AppDataField("<<APPDATA.Results>>", {}, len))
    prediction_jobs: _AppDataField[List[PredictionJob], int] =\
        field(init=False, default_factory=lambda: _AppDataField("<<APPDATA.PredictionJobs>>", [], len))

    def gather_events(self):
        return [
            getattr(self, f.name).event
            for f in fields(self)
            if getattr(self, f.name).changed
        ]


AppData = _AppData()
