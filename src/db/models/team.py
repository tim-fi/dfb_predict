from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy

from ..core import Model
from .association_tables import team_season_association_table


__all__ = (
    "Team",
)


class Team(Model):
    __tablename__ = "teams"

    shortname = Column(String)
    name = Column(String)

    seasons = relationship("Season", secondary=team_season_association_table, back_populates="teams")
    # match_participations = relationship("MatchParticipation")

    matches = association_proxy("match_participations", "match")

    def __repr__(self) -> str:
        return f"<Team(name={self.name}, seasons={self.seasons})>"

    def __str__(self) -> str:
        return f'{self.name} [{self.shortname}]' if self.shortname != self.name and self.shortname not in self.name else self.name
