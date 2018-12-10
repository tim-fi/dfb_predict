from abc import ABCMeta, abstractmethod


__all__ = (
    "Predictor",
)


class Predictor(metaclass=ABCMeta):
    registry = dict()

    def __init_subclass__(cls, verbose_name=None):
        Predictor.registry[verbose_name or cls.__name__] = cls

    @abstractmethod
    def calculate_model(self, selector, session):
        raise NotImplementedError()

    @abstractmethod
    def make_prediction(self, host_id, guest_id):
        raise NotImplementedError()
