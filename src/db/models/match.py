from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..core import Model


__all__ = (
    "Match",
)


class Match(Model):
    __tablename__ = "matches"

    date = Column(DateTime)

    is_finished = Column(Boolean)

    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", backref="matches")

    host_id = Column(Integer, ForeignKey("teams.id"))
    host = relationship("Team", backref="hosted_matches", primaryjoin="Match.host_id == Team.id")

    guest_id = Column(Integer, ForeignKey("teams.id"))
    guest = relationship("Team", backref="guest_matches", primaryjoin="Match.guest_id == Team.id")

    half_time_result_id = Column(Integer, ForeignKey("results.id"))
    half_time_result = relationship("Result", primaryjoin="Match.half_time_result_id == Result.id")

    end_result_id = Column(Integer, ForeignKey("results.id"))
    end_result = relationship("Result", primaryjoin="Match.end_result_id == Result.id")

    results = relationship("Result", backref="match", primaryjoin="Match.end_result_id == Result.id or Match.half_time_result_id == Result.id")

    def __repr__(self) -> str:
        return f"<Match(datetime={self.date}, host={str(self.host)}, guest={str(self.guest)}, end_result={str(self.end_result)})>"

    def __str__(self) -> str:
        return f"{self.date} -- {repr(str(self.group))} -- {str(self.host)} vs. {str(self.guest)} -- {str(self.end_result) if self.is_finished else 'not finished'}"
