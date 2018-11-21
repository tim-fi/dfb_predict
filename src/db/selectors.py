from abc import ABCMeta, abstractmethod

from sqlalchemy import and_, or_


class Selector(metaclass=ABCMeta):
    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    @abstractmethod
    def to_filter(self):
        ...


class And(Selector):
    def __init__(self, *selectors):
        self._selectors = selectors

    def __and__(self, other):
        self._selectors.append(other)
        return self

    def to_filter(self):
        return and_(*[
            selector.to_filter()
            for selector in self._selectors
        ])


class Or(Selector):
    def __init__(self, *selectors):
        self._selectors = selectors

    def __or__(self, other):
        self._selectors.append(other)
        return self

    def to_filter(self):
        return or_(*[
            selector.to_filter()
            for selector in self._selectors
        ])


class Custom(Selector):
    def __init__(self, filter):
        self._filter

    def to_filter(self,):
        return self._filter

