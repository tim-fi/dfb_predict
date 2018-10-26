from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ..core import DB
from .association_tables import team_season_association_table


__all__ = (
    "Team",
)


class Team(DB.Model):  # type: ignore
    __tablename__ = "teams"

    name = Column(String)

    seasons = relationship("Season", secondary=team_season_association_table, back_populates="teams")

    def __repr__(self) -> str:
        return f"<Team(name={self.name}, seasons={self.seasons})>"

    def __str__(self) -> str:
        return self.name
