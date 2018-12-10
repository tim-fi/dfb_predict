from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from .models import Group, Season, Match, Team


__all__ = (
    "RangeSelector",
    "RangePoint"
)


base_query = Query(Match).join(Match.group, Group.season)


@dataclass
class RangePoint:
    year: Optional[int] = None
    group: Optional[int] = None

    def is_null(self):
        return self.year is None and self.group is None

    def is_partial(self):
        return (self.year is None) ^ (self.group is None)


class RangeSelector:
    def __init__(self, start: RangePoint = None, end: RangePoint = None) -> None:
        self._start = start or RangePoint()
        self._end = end or RangePoint()

    def build_team_query(self) -> Query:
        return Query(Team)

    def build_match_query(self) -> Query:
        filters = [
            Match.is_finished,
        ]
        if not self._end.is_null() and not self._end.is_partial():
            filters.append(
                or_(
                    Season.year < self._end.year,
                    and_(
                        Season.year == self._end.year,
                        Group.order_id <= self._end.group
                    )
                ),
            )
        if not self._start.is_null() and not self._start.is_partial():
            filters.append(
                or_(
                    Season.year > self._start.year,
                    and_(
                        Season.year == self._start.year,
                        Group.order_id >= self._start.group
                    )
                )
            )

        return base_query.filter(and_(*filters))
