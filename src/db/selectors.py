from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from .models import Group, Season, Match, Team, MatchParticipation


__all__ = (
    "RangeSelector",
    "RangePoint"
)


@dataclass
class RangePoint:
    """Edge of a selection"""
    year: Optional[int] = None
    group: Optional[int] = None

    def is_null(self):
        return self.year is None and self.group is None

    def is_partial(self):
        return (self.year is None) ^ (self.group is None)

    def __str__(self):
        return f"{self.year}{f'/{self.group}' if self.group is not None else ''}"


class RangeSelector:
    """Complete selection"""

    def __init__(self, start: RangePoint = None, end: RangePoint = None) -> None:
        self._start = start or RangePoint()
        self._end = end or RangePoint()
        if not self.is_valid:
            raise TypeError(f"Invalid selection:\nfrom {start} to {end}")

    @property
    def is_valid(self) -> bool:
        return (
            RangeSelector._null_checked_lte(self._start.year, self._end.year) and
            (RangeSelector._null_checked_lte(self._start.group, self._end.group) if self._start.year == self._end.year else True)
        )

    @staticmethod
    def _null_checked_lte(start: Optional[int], end: Optional[int]):
        return start is None or end is None or start <= end

    def copy(self, other: RangeSelector) -> None:
        self._start = other._start
        self._end = other._end

    def build_team_query(self) -> Query:
        """Build a query for Teams with matches in selected timespace."""
        filters = []
        if not self._end.is_null():
            if not self._end.is_partial():
                filters.append(
                    or_(
                        Team.seasons.any(Season.year < self._end.year),
                        and_(
                            Team.seasons.any(Season.year == self._end.year),
                            Team.match_participations.any(Group.order_id <= self._end.group)
                        )
                    ),
                )
            elif self._end.year is not None:
                filters.append(
                    Team.seasons.any(Season.year <= self._end.year)
                )
        if not self._start.is_null():
            if not self._start.is_partial():
                filters.append(
                    or_(
                        Team.seasons.any(Season.year > self._start.year),
                        and_(
                            Team.seasons.any(Season.year == self._start.year),
                            Team.match_participations.any(Group.order_id >= self._start.group)
                        )
                    ),
                )
            elif self._start.year is not None:
                filters.append(
                    Team.seasons.any(Season.year >= self._start.year)
                )
        return Query(Team).join(MatchParticipation, Match, Group).filter(and_(*filters))

    def build_match_query(self) -> Query:
        """Build a query for Matches in selected timespace."""
        filters = [
            Match.is_finished,
        ]
        if not self._end.is_null():
            if not self._end.is_partial():
                filters.append(
                    or_(
                        Season.year < self._end.year,
                        and_(
                            Season.year == self._end.year,
                            Group.order_id <= self._end.group
                        )
                    ),
                )
            elif self._end.year is not None:
                filters.append(
                    Season.year <= self._end.year
                )
        if not self._start.is_null():
            if not self._start.is_partial():
                filters.append(
                    or_(
                        Season.year > self._start.year,
                        and_(
                            Season.year == self._start.year,
                            Group.order_id >= self._start.group
                        )
                    ),
                )
            elif self._start.year is not None:
                filters.append(
                    Season.year >= self._start.year
                )
        return Query(Match).join(Match.group, Group.season).filter(and_(*filters))
