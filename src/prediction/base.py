from __future__ import annotations

from abc import ABCMeta, abstractmethod, abstractstaticmethod
from dataclasses import dataclass, InitVar, field
from typing import Optional, Type, ClassVar, Dict, Any, TypeVar, List, Tuple
<<<<<<< HEAD
=======
import json
>>>>>>> 727cf36179d0d3f94458b620bcecd56ea9576a87

from sqlalchemy.orm import Session

from ..db import RangeSelector, RangePoint


__all__ = (
    "Model",
    "PredictionResult"
)

T = TypeVar('T')


@dataclass(frozen=True)
class PredictionResult:
    model_type: str
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

    @property
    def reliability(self):
        return max(0, 1 - abs(self.host_win_propability + self.guest_win_propability + self.draw_propability - 1))

    def __str__(self):
        return "\n".join([
            "----------------------------------------",
            f"Game: {self.host_name} vs. {self.guest_name}",
            "----------------------------------------",
            f"Predicted via {self.model_type} model.",
            "----------------------------------------",
            "General outcome propabilies:",
            f" * host win:  {self.host_win_propability:.1%}",
            f" * draw:      {self.draw_propability:.1%}",
            f" * guest win: {self.guest_win_propability:.1%}",
            f" -> Most propable outcome: {['draw', 'host win', 'guest win'][(self.host_win + self.guest_win * 2 + self.draw * 3) % 3]}",
            "----------------------------------------",
            f"Reliability: {self.reliability:.1%}",
            "----------------------------------------",
        ])


@dataclass
class Model(metaclass=ABCMeta):
    registry: ClassVar[Dict[str, Type[Model]]] = dict()
    verbose_name: ClassVar[str] = ""
    selector: RangeSelector
    session: InitVar[Session]
    features: Any = field(init=False)
    teams: List[str] = field(init=False)

    def __init_subclass__(cls, verbose_name: Optional[str] = None) -> None:
        cls.verbose_name = verbose_name or cls.__name__
        Model.registry[cls.verbose_name] = cls

    def __post_init__(self, session: Session) -> None:
        self.features, self.teams = self.calculate_model(self.selector, session)

    @abstractstaticmethod
    def calculate_model(selector: RangeSelector, session: Session) -> Tuple[Any, List[str]]:
        raise NotImplementedError()

    @abstractmethod
    def make_prediction(self, host_name: str, guest_name: str) -> PredictionResult:
        raise NotImplementedError()
