from sqlalchemy import Column, Integer, Boolean

from ..core import Model


__all__ = (
    "Result",
)


class Result(Model):
    __tablename__ = "results"

    host_points = Column(Integer)
    guest_points = Column(Integer)

    is_end = Column(Boolean)

    def __repr__(self) -> str:
        return f"<Result(match={self.match.id}, host_points={self.host_points}, guest_points={self.guest_points}, is_end={self.is_end})>"

    def __str__(self) -> str:
        return f"{self.host_points}:{self.guest_points}"
