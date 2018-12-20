from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ..db import RangeSelector


__all__ = (
    "Predictor",
    "PredictionResult"
)


@dataclass(frozen=True)
class PredictionResult:
    host_name: str
    guest_name: str

    host_win_propability: float
    draw_propability: float
    guest_win_propability: float

    @property
    def host_win(self):
        return self.host_win_propability > self.guest_win_propability and self.host_win_propability > self.draw_propability

    @property
    def draw(self):
        return self.draw_propability > self.guest_win_propability and self.host_win_propability > self.guest_win_propability

    @property
    def guest_win(self):
        return self.guest_win_propability > self.host_win_propability and self.guest_win_propability > self.draw_propability

    def __str__(self):
        return "\n".join([
            "----------------------------------------",
            f"Game: {self.host_name} vs. {self.guest_name}",
            "----------------------------------------",
            "General outcome propabilies:",
            f" * host win:  {self.host_win_propability:.1%}",
            f" * draw:      {self.draw_propability:.1%}",
            f" * guest win: {self.guest_win_propability:.1%}",
            f" -> Most propable outcome: {['draw', 'host win', 'guest win'][(self.host_win + self.guest_win * 2 + self.draw * 3) % 3]}",
            "----------------------------------------",
        ])


class Predictor(metaclass=ABCMeta):
    registry = dict()

    def __init_subclass__(cls, verbose_name: Optional[str] = None) -> None:
        Predictor.registry[verbose_name or cls.__name__] = cls

    @abstractmethod
    def calculate_model(self, selector: RangeSelector, session: Session) -> None:
        raise NotImplementedError()

    @abstractmethod
    def make_prediction(self, host_name: str, guest_name: str) -> PredictionResult:
        raise NotImplementedError()
