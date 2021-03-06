from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Type, ClassVar, Dict, List

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker, scoped_session, Session, Query
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import as_declarative


__all__ = (
    "DB",
    "Model"
)


@as_declarative()
class Model:
    id = Column(Integer, primary_key=True, unique=True)


class _DB_Meta(type):
    _instances: ClassVar[Dict[str, _DB]] = {}  # noqa: F821

    def __call__(cls, engine_descriptor=None):
        if engine_descriptor in _DB_Meta._instances:
            return _DB_Meta._instances[engine_descriptor]
        else:
            _DB_Meta._instances[engine_descriptor] = instance = super().__call__(engine_descriptor)
            return instance


class _DB(metaclass=_DB_Meta):
    def __init__(self, engine_descriptor: str) -> None:
        self.configure(engine_descriptor)

    def configure(self, engine_descriptor: str) -> None:
        if hasattr(self, "_engine"):
            del self._ScopedSession
            del self._Session
            del self._engine
        self._engine: Engine = create_engine(engine_descriptor)
        self._Session: Type[Session] = sessionmaker(bind=self._engine)
        self._ScopedSession: Type[Session] = scoped_session(self._Session)

    def create_tables(self) -> None:
        Model.metadata.create_all(self._engine)  # type: ignore

    def drop_tables(self) -> None:
        Model.metadata.drop_all(self._engine)  # type: ignore

    @contextmanager
    def get_session(self, *args, scoped: bool = False, **kwargs) -> Generator[Session, None, None]:
        session = self._Session(*args, **kwargs) if not scoped else self._ScopedSession(*args, **kwargs)
        try:
            yield session
        except:  # noqa: E722
            # here the bare except is used simply to intercept exceptions, to rollback the changes that may have
            # happened in the session before closing it.
            # This is actually the recommended way to do this in the SQLAlchemy docs!
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()


project_dir = os.getcwd()
database_path = os.path.join(project_dir, "db.sqlite3")
DB = _DB(f"sqlite:///{database_path}")
