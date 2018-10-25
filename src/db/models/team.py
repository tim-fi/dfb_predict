from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ..core import DB
from .association_tables import team_season_association_table


__all__ = (
    "Team",
)


class Team(DB.Model):
    __tablename__ = "teams"

    name = Column(String)

    seasons = relationship("Season", secondary=team_season_association_table, back_populates="teams")
