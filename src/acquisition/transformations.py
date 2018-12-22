from typing import TypeVar, Callable, List, Type, overload, Dict, Any

from sqlalchemy.orm import Session

from .core import Transformation, Pipeline


__all__ = (
    "Get",
    "Custom",
    "Attr",
    "Filter",
    "Gather",
    "GetOrCreate",
    "Create",
    "CreateMultiple"
)


T = TypeVar("T")
K = TypeVar("K")
M = TypeVar("M")


@overload
def Get(pipeline, data: Dict[K, T], session, key: K) -> T:
    ...


@overload  # noqa: F811
def Get(pipeline, data: List[T], session, key: int) -> T:
    ...


@Transformation.from_func  # noqa: F811
def Get(pipeline: Pipeline, data, session: Session, key):
    """Get a single value from collection by index operation

    :param key: index to get from data

    """
    return data[key]


@Transformation.from_func
def Custom(pipeline: Pipeline, data: T, session: Session, func: Callable[[T], K]) -> K:
    """ Apply custom function

    :param func: custom func to apply

    """
    return func(data)


@Transformation.from_func
def Attr(pipeline: Pipeline, data: Any, session: Session, key: str) -> Any:
    """Get a single attribute from object

    :param key: attribute to get from obj.

    """
    return getattr(data, key)


@Transformation.from_func
def Filter(pipeline: Pipeline, data: List[T], session: Session, pred: Callable[[T], bool]) -> List[T]:
    """Filter a given list via a predicate

    :param pred: predicate to filter by

    """
    return [row for row in data if pred(row)]


@Transformation.from_func
def Gather(pipeline: Pipeline, data: Any, session: Session, *names: List[str]) -> Dict:
    """Gather multiple different values into a list

    :param names: keywords to reference

    """
    return {name: data[name] for name in names}


@Transformation.from_func
def GetOrCreate(pipeline: Pipeline, data: Any, session: Session, model: Type[M]) -> M:
    """Get or create an instant model from data

    :param model: model to get or create an instance for

    """
    kwargs = pipeline.generate_kwargs(model, data, session)
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)  # type: ignore
        session.add(instance)
        session.commit()
    return instance


@Transformation.from_func
def Create(pipeline: Pipeline, data: Any, session: Session, model: Type[M]) -> M:
    """Create an instance model from data

    :param model: model to create an instance for

    """
    instance = pipeline.create(model, data, session)
    session.add(instance)
    session.commit()
    return instance


@Transformation.from_func
def CreateMultiple(pipeline: Pipeline, data: Any, session: Session, model: Type[M]) -> List[M]:
    """Create multiple instances of a  model from data

    :param model: model to create an instances for

    """
    instances = []
    for instance_data in data:
        instances.append(pipeline.create(model, instance_data, session))
    session.add_all(instances)
    session.commit()
    return instances
