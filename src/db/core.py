from contextlib import contextmanager
from typing import ContextManager

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import as_declarative


__all__ = (
    "DB",
)


class _DB_Meta(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if _DB_Meta._instance is not None:
            if len(args) + len(kwargs) > 0:
                raise RuntimeError("Tried to re-instantiate DB...")
            else:
                return _DB_Meta._instance
        else:
            _DB_Meta._instance = super().__call__(*args, **kwargs)
            return _DB_Meta._instance


class _DB(metaclass=_DB_Meta):
    @as_declarative()
    class Model:
        id = Column(Integer, primary_key=True, unique=True)

    def __init__(self, engine_descriptor: str) -> None:
        self.configure(engine_descriptor)

    def configure(self, engine_descriptor: str) -> None:
        if hasattr(self, "_engine"):
            del self._ScopedSession
            del self._Session
            del self._engine
        self._engine = create_engine(engine_descriptor)
        self._Session = sessionmaker(bind=self._engine)
        self._ScopedSession = scoped_session(self._Session)

    def create_tables(self) -> None:
        self.drop_tables()
        self.Model.metadata.create_all(self._engine)

    def drop_tables(self) -> None:
        self.Model.metadata.drop_all(self._engine)

    @contextmanager
    def get_session(self, *args, scoped: bool = False, **kwargs) -> ContextManager[Session]:
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


DB = _DB("sqlite:///:memory:")
