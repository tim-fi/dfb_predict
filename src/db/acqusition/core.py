from abc import ABCMeta, abstractstaticmethod


__all__ = (
    "Pipeline",
    "Transformation",
    "Transformations",
)


class Pipeline:
    def __init__(self, transformations=None):
        self._transformations = transformations or {}

    def add_transformation(self, model, transformations):
        self._transformations[model] = transformations

    def create(self, model, data, session):
        return model(
            **self.generate_kwargs(model, data, session)
        )

    def generate_kwargs(self, model, data, session):
        return {
            key: transformation(self, data, session)
            for key, transformation in self._transformations.items()
        }

    def create_multiple(self, model, data, session):
        return (
            self.create(model, row, session)
            for row in data
        )


class Transformation(metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._prev = None

    def __call__(self, pipeline, data, session):
        data = self._prev(pipeline, data, session) if self._prev is not None else data 
        return self.apply(pipeline, data, session, *self._args, **self._kwargs)

    def __ror__(self, other):
        if not isinstance(other, Transformation):
            raise TypeError("Can only chain Transformations with Transformations.")
        self._prev = other
        return self

    @abstractstaticmethod
    def apply(pipeline, data, session, *args, **kwargs):
        raise NotImplementedError("Must implement apply for a transfomation.")

    @staticmethod
    def from_func(func):
        class Class(Transformation):
            @staticmethod
            def apply(pipeline, data, session, *args, **kwargs):
                return func(pipeline, data, session, *args, **kwargs)
        Class.__name__ = func.__name__
        return Class


class Transformations:
    @Transformation.from_func
    def Get(pipeline, data, session, key):
        return data[key]

    @Transformation.from_func
    def Custom(pipeline, data, session, func):
        return func(data)

    @Transformation.from_func
    def Attr(pipeline, data, session, key):
        return getattr(data, key)

    @Transformation.from_func
    def Filter(pipeline, data, session, pred):
        return [row for row in data if pred(row)]

    @Transformation.from_func
    def GetOrCreate(pipeline, data, session, model):
        kwargs = pipeline.generate_kwargs(model, data, session)
        instance = session.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
        return instance

    @Transformation.from_func
    def Create(pipeline, data, session, model):
        instance = pipeline.create(model, pipeline, data, session)
        session.add(instance)
        session.commit()
        return instance
