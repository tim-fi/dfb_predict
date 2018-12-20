from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy.orm import relationship

from ..core import Model
from .association_tables import team_season_association_table


__all__ = (
    "Season",
)


class Season(Model):
    __tablename__ = "seasons"

    year = Column(Integer)
    enabled = Column(Boolean, default=True)

    teams = relationship("Team", secondary=team_season_association_table, back_populates="seasons")

    def __repr__(self):
        return f"<Season(year={self.year})>"

    def __str__(self):
        return f"{self.year}/{(self.year % 100) + 1}"
