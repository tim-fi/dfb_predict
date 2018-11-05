import os

from contextlib import contextmanager
from typing import Generator, Type

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import as_declarative


__all__ = (
    "DB",
    "Model"
)


@as_declarative()
class Model:
    id = Column(Integer, primary_key=True, unique=True)


class _DB_Meta(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if _DB_Meta._instance is not None:
            if len(args) + len(kwargs) > 0:
                raise RuntimeError(f"Tried to re-instantiate {cls}...")
            else:
                return _DB_Meta._instance[cls]
        else:
            _DB_Meta._instance[cls] = instance = super().__call__(*args, **kwargs)
            return instance


class _DB(metaclass=_DB_Meta):
    def __init__(self, engine_descriptor: str) -> None:
        self.configure(engine_descriptor)

    def configure(self, engine_descriptor: str) -> None:
        if hasattr(self, "_engine"):
            del self._ScopedSession
            del self._Session
            del self._engine
        self._engine = create_engine(engine_descriptor)
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
        except:
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()


project_dir = os.getcwd()
database_path = os.path.join(project_dir, "data.db")
DB = _DB(f"sqlite:///{database_path}")
