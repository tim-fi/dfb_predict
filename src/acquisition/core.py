from __future__ import annotations

from abc import ABCMeta, abstractstaticmethod
from typing import Dict, TypeVar, Optional, Generic, Type, Any, Generator

from sqlalchemy.orm import Session


__all__ = (
    "Pipeline",
    "Transformation",
)


M = TypeVar("M")
_M = TypeVar["_M"]


class Pipeline(Generic[M]):
    def __init__(self, transformations: Optional[Dict[Type[M], Dict[str, Transformation]]] = None) -> None:
        self._transformations = transformations or {}

    def add_transformation(self, model: Type[M], transformations: Dict[str, Transformation]) -> None:
        """Add a transformation map for a given model

        :param model: model to add transformation map for
        :param transformations: transformation map to add
        
        """
        self._transformations[model] = transformations

    def create(self, model: Type[_M], data: Any, session: Session) -> _M:
        """Create a single instance of a given model based on the given data
        
        :param model: target model
        :param data: data to use in creation process
        :param session: DB session to use for queries

        """
        return model(
            **self.generate_kwargs(model, data, session)
        )

    def generate_kwargs(self, model: Type[M], data: Any, session: Session) -> Dict[str, Any]:
        """Generate required kwargs for model instantiation based on the given data 
        and the predefined transformation map
        
        :param model: target model
        :param data: data to use in creation process
        :param session: DB session to use for queries

        """
        return {
            key: transformation(self, data, session)
            for key, transformation in self._transformations[model].items()
        }

    def create_multiple(self, model: Type[_M], data: Any, session: Session) -> Generator[_M, None, None]:
        """Create multiple instances of a given model based on the given data
        
        :param model: target model
        :param data: data to use in creation process
        :param session: DB session to use for queries

        """
        return (
            self.create(model, row, session)
            for row in data
        )


class Transformation(metaclass=ABCMeta):
    """ A transformation represents a single function or 
    chain thereof with the sole purpose to transform/"mung" data.
    
    """
    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs
        self._prev = None

    def __call__(self, pipeline: Pipeline, data: Any, session: Session) -> Any:
        data = self._prev(pipeline, data, session) if self._prev is not None else data 
        return self.apply(pipeline, data, session, *self._args, **self._kwargs)

    def __ror__(self, other: Transformation) -> Transformation:
        if not isinstance(other, Transformation):
            raise TypeError("Can only chain Transformations with Transformations.")
        self._prev = other
        return self

    @abstractstaticmethod
    def apply(pipeline: Pipeline, data: Any, session: Session, *args, **kwargs) -> Any:
        """ Functin to apply to data -- override to make use of

        :param pipeline: parent pipeline
        :param data: target data
        :param session: DB session to interact with
        :param *args: additional positional arguments
        :param **kwargs: additional keyword arguments

        
        """
        raise NotImplementedError("Must implement apply for a transfomation.")

    @staticmethod
    def from_func(func):
        """Decorator , which wraps a single function with a Transformation.
        :param func: function to be wrapped
        
        """
        new_type = type().__new__(
            func.__name__,
            (Transformation,),
            {
                "apply": staticmethod(func),
                "__docs__": func.__doc__
            }
        )
        return new_type
