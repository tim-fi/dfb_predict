from sqlalchemy import Table, Integer, Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..core import Model


__all__ = (
    "team_season_association_table",
    "MatchParticipation"
)


team_season_association_table = Table(
    "team_seasons_association", Model.metadata,  # type: ignore
    Column("season_id", Integer, ForeignKey("seasons.id")),
    Column("team_id", Integer, ForeignKey("teams.id")),
)


class MatchParticipation(Model):
    __tablename__ = "match_participations"

    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", backref="match_participations")

    match_id = Column(Integer, ForeignKey("matches.id"))
    match = relationship("Match", backref="match_participations")

    hosted = Column(Boolean)
