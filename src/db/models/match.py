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

    host_points = Column(Integer)
    guest_points = Column(Integer)

    def __repr__(self) -> str:
        return f"<Match(datetime={self.date}, host={str(self.host)}, guest={str(self.guest)}, host_points={self.host_points}, guest_points={self.guest_points})>"

    def __str__(self) -> str:
        return f"{self.date} -- {repr(str(self.group))} -- {str(self.host)} vs. {str(self.guest)} -- {f'{self.host_points}:{self.guest_points}' if self.is_finished else 'not finished'}"
