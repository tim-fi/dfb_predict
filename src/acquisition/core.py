from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Dict, TypeVar, Optional, Generic, Type, Any, Generator, Callable

from sqlalchemy.orm import Session


__all__ = (
    "Pipeline",
    "Transformation",
)


M = TypeVar("M", covariant=True)


class Pipeline(Generic[M]):
    def __init__(self, transformations: Optional[Dict[Type[M], Dict[str, Transformation]]] = None) -> None:  # noqa: F821
        self._transformations = transformations or {}

    def add_transformation(self, model: Type[M], transformations: Dict[str, Transformation]) -> None:  # noqa: F821
        """Add a transformation map for a given model

        :param model: model to add transformation map for
        :param transformations: transformation map to add

        """
        self._transformations[model] = transformations

    def create(self, model: Type[M], data: Any, session: Session) -> M:
        """Create a single instance of a given model based on the given data

        :param model: target model
        :param data: data to use in creation process
        :param session: DB session to use for queries

        """
        return model(  # type: ignore
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

    def generate_kwarg(self, model: Type[M], key: str, data: Any, session: Session) -> Any:
        """Generate a single kwarg for model instantiation based on the given data
        and the predefined transformation map

        :param model: target model
        :param key: the kwarg to generate
        :param data: data to use in creation process
        :param session: DB session to use for queries

        """
        return self._transformations[model][key](self, data, session)

    def create_multiple(self, model: Type[M], data: Any, session: Session) -> Generator[M, None, None]:
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
    """
    A transformation represents a single function or
    chain thereof with the sole purpose to transform/"munge" data.
    """
    def __init__(self, *args, **kwargs) -> None:
        # this 'cast' to a list from the normal tuple is done to support the
        # _CONCAT transformation type
        self._args = list(args)
        self._kwargs = kwargs

    def __call__(self, pipeline: Pipeline, data: Any, session: Session) -> Any:
        return self.apply(pipeline, data, session, *self._args, **self._kwargs)

    def __or__(self, other: Transformation) -> Transformation:  # noqa: F821
        if not isinstance(other, Transformation):
            raise TypeError("Can only chain Transformations with Transformations.")
        if isinstance(self, _CONCAT):
            self._args.append(other)
            return self
        else:
            return _CONCAT(self, other)

    @staticmethod
    @abstractmethod
    def apply(pipeline: Pipeline, data: Any, session: Session, *args, **kwargs) -> Any:
        """Functin to apply to data -- override to make use of

        :param pipeline: parent pipeline
        :param data: target data
        :param session: DB session to interact with
        :param *args: additional positional arguments
        :param **kwargs: additional keyword arguments

        """
        raise NotImplementedError("Must implement apply for a transfomation.")

    @staticmethod
    def from_func(func: Callable) -> Type[Transformation]:  # noqa: F821
        """Decorator , which wraps a single function with a Transformation.
        :param func: function to be wrapped

        """
        new_type = type(
            func.__name__,
            (Transformation,),
            {
                "apply": staticmethod(func),
                "__doc__": func.__doc__
            }
        )
        return new_type


@Transformation.from_func
def _CONCAT(pipeline: Pipeline, data: Any, session: Session, *transformations: Transformation) -> Any:
    """A simple transformation that represent the concatenation between two or more other transformations.

    :param *transformations: transformation to concatenate

    """
    res = data
    for transformation in transformations:
        res = transformation(pipeline, res, session)
    return res
