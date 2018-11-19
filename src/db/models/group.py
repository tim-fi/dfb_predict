from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..core import Model


__all__ = (
    "Group",
)


class Group(Model):
    __tablename__ = "groups"

    order_id = Column(Integer)

    season_id = Column(ForeignKey("seasons.id"))
    season = relationship("Season", backref="groups")

    def __repr__(self):
        return f"<Group(order_id={self.order_id}>"

    def __str__(self):
        return f"{self.order_id}-ter Spieltag {str(self.season)}"
