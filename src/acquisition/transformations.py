from typing import TypeVar, Callable, List, Type, overload, Dict, Any, Optional, Sequence, Mapping, Iterable

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
    "CreateMultiple",
    "If",
    "Constant",
)


T = TypeVar("T")
K = TypeVar("K")
M = TypeVar("M")


@overload
def Get(pipeline, data: Mapping[K, T], session, key: K) -> T:
    ...


@overload  # noqa: F811
def Get(pipeline, data: Sequence[T], session, key: int) -> T:
    ...


@Transformation.from_func  # noqa: F811
def Get(pipeline: Pipeline, data, session: Session, key):
    """Get a single value from collection by index operation

    :param key: index to get from data

    """
    return data[key]


@Transformation.from_func
def Custom(pipeline: Pipeline, data: T, session: Session, func: Callable[[T], K]) -> K:
    """Apply custom function

    :param func: custom func to apply

    """
    return func(data)


@Transformation.from_func
def Constant(pipeline: Pipeline, data: Any, session: Session, constant: T) -> T:
    """Return a constant

    :param constant: constant to return

    """
    return constant


@Transformation.from_func
def Attr(pipeline: Pipeline, data: Any, session: Session, key: str) -> Any:
    """Get a single attribute from object

    :param key: attribute to get from obj.

    """
    return getattr(data, key)


@Transformation.from_func
def Filter(pipeline: Pipeline, data: Iterable[T], session: Session, pred: Callable[[T], bool]) -> List[T]:
    """Filter a list via a predicate

    :param pred: predicate to filter by

    """
    return [x for x in iter(data) if pred(x)]


@Transformation.from_func
def Map(pipeline: Pipeline, data: Iterable[T], session: Session, func: Callable[[T], K]) -> List[K]:
    """Apply a function to each element in list

    :param func: func to apply

    """
    return [func(x) for x in iter(data)]


@Transformation.from_func
def Gather(pipeline: Pipeline, data: Mapping[T, K], session: Session, *names: Sequence[T]) -> Dict[T, K]:
    """Gather multiple different values into a list

    :param names: keywords to reference

    """
    return {name: data[name] for name in names}


@Transformation.from_func
def If(pipeline: Pipeline, data: T, session: Session, cond: Callable[[T], bool], then: Transformation, else_: Optional[Transformation] = None) -> Any:
    """Condtionally execute or branch between Transformations

    :param cond: the condition on which to branch/execute
    :param then: Transformation to execute on True-case
    :param else_: Transformation to execute on False-case (default: None)

    """
    if cond(data):
        return then(pipeline, data, session)
    elif else_ is not None:
        return else_(pipeline, data, session)
    else:
        return None


@Transformation.from_func
def GetOrCreate(pipeline: Pipeline, data: Any, session: Session, model: Type[M], match_targets: Optional[List[str]] = None) -> M:
    """Get or create an instant model from data

    :param model: model to get or create an instance for
    :param match_targets: fields to match on (default: None)

    """
    if match_targets is None:
        kwargs = pipeline.generate_kwargs(model, data, session)
    else:
        kwargs = {
            key: pipeline.generate_kwarg(model, key, data, session)
            for key in match_targets
        }

    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        if match_targets is not None:
            kwargs = pipeline.generate_kwargs(model, data, session)
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
def CreateMultiple(pipeline: Pipeline, data: Sequence[Any], session: Session, model: Type[M]) -> List[M]:
    """Create multiple instances of a  model from data

    :param model: model to create an instances for

    """
    instances = []
    for instance_data in data:
        instances.append(pipeline.create(model, instance_data, session))
    session.add_all(instances)
    session.commit()
    return instances
