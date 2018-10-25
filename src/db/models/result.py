from sqlalchemy import Column, Integer, Boolean

from ..core import DB


__all__ = (
    "Result",
)


class Result(DB.Model):
    __tablename__ = "results"

    host_points = Column(Integer)
    guest_points = Column(Integer)

    is_end = Column(Boolean)
