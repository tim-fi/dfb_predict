from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from ..core import DB
from .associtation_tables import team_season_association_table


__all__ = (
    "Season",
)


class Season(DB.Model):
    __tablename__ = "seasons"

    year = Column(Integer)

    teams = relationship("Team", secondary=team_season_association_table, back_populates="seasons")
