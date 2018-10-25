from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core import DB


__all__ = (
    "Match",
)


class Match(DB.Model):
    __tablename__ = "matches"

    date = Column(DateTime)

    season_id = Column(Integer, ForeignKey("seasons.id"))
    season = relationship("Season", backref="matches")

    host_id = Column(Integer, ForeignKey("teams.id"))
    host = relationship("Team", backref="hosted_matches", primaryjoin="Match.host_id == Team.id")

    guest_id = Column(Integer, ForeignKey("teams.id"))
    guest = relationship("Team", backref="guest_matches", primaryjoin="Match.guest_id == Team.id")

    half_time_result_id = Column(Integer, ForeignKey("results.id"))
    half_time_result = relationship("Result", primaryjoin="Match.half_time_result_id == Result.id")

    end_result_id = Column(Integer, ForeignKey("results.id"))
    end_result = relationship("Result", primaryjoin="Match.end_result_id == Result.id")

    results = relationship("Result", backref="match", primaryjoin="Match.end_result_id == Result.id | Match.half_time_result_id == Result.id")
