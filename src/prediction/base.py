from abc import ABCMeta, abstractmethod


__all__ = (
    "PREDICTOR_CLASS_REGISTRY",
    "BasePredictor"
)


PREDICTOR_CLASS_REGISTRY = dict()


class BasePredictor(metaclass=ABCMeta):
    def __init_subclass__(cls, verbose_name=None):
        PREDICTOR_CLASS_REGISTRY[verbose_name or cls.__name__] = cls

    @abstractmethod
    def calculate_model(self, selector, session):
        raise NotImplementedError()

    @abstractmethod
    def make_prediction(self, host_id, guest_id):
        raise NotImplementedError()
