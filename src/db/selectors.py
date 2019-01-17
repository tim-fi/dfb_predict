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

    @classmethod
    def parse_from_string(cls, s: Optional[str]) -> RangePoint:
        """Parse a RangePoint from a string

        This function parses a RangePoint from a string
        following the format: "<year>[/<group>]"

        :param s: the string to parse
        :returns: the parsed RangePoint

        """
        year = None if s is None else int(s) if "/" not in s else int(s[:4])
        group = None if s is None or "/" not in s else int(s[5:])
        return cls(year, group)

    def is_null(self):
        return self.year is None and self.group is None

    def is_partial(self):
        return (self.year is None) ^ (self.group is None)

    def __str__(self):
        return f"{self.year}{f'/{self.group}' if self.group is not None else ''}"

    def build_filter(self, compare_op: str, *, ignore_groups: bool = False):
        if not self.is_null():
            if not self.is_partial() and not ignore_groups:
                return or_(
                    getattr(Season.year, f"__{compare_op}t__")(self.year),
                    and_(
                        Season.year == self.year,
                        getattr(Group.order_id, f"__{compare_op}e__")(self.group)
                    )
                )
            elif self.year is not None:
                return getattr(Season.year, f"__{compare_op}e__")(self.year)
        return and_()


class RangeSelector:
    """Complete selection"""
    __slots__ = ("_start", "_end")

    def __eq__(self, other: RangePoint) -> bool:
        return isinstance(other, RangeSelector) and self._start == other._start and self._end == other._end

    def __neq__(self, other: RangePoint) -> bool:
        return not isinstance(other, RangeSelector) or self._start != other._start or self._end != other._end

    def __init__(self, start: Optional[RangePoint] = None, end: Optional[RangePoint] = None) -> None:
        self._start = start or RangePoint()
        self._end = end or RangePoint()
        if not self.is_valid:
            raise TypeError(f"Invalid selection:\nfrom {self.start} to {self.end}")

    def __str__(self):
        end_null = self._end.is_null()
        start_null = self._start.is_null()
        if start_null and end_null:
            return "all"
        elif start_null and not end_null:
            return f"until {str(self._end)}"
        elif not start_null and end_null:
            return f"from {str(self._start)}"
        elif self._end != self._start:
            return f"from {str(self._start)} until {str(self._end)}"
        else:
            return str(self._start)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def is_valid(self) -> bool:
        return (
            RangeSelector._null_checked_lte(self._start.year, self._end.year) and  # noqa W504
            (RangeSelector._null_checked_lte(self._start.group, self._end.group) if self._start.year == self._end.year else True)
        )

    @staticmethod
    def _null_checked_lte(start: Optional[int], end: Optional[int]):
        return start is None or end is None or start <= end

    def copy(self, other: RangeSelector) -> None:  # noqa: F821
        self._start = other._start
        self._end = other._end

    def build_filters(self, *, ignore_groups: bool = False):
        """Build a filter to match data in timespace."""
        return and_(
            self._start.build_filter("g", ignore_groups=ignore_groups),
            self._end.build_filter("l", ignore_groups=ignore_groups)
        )

    def build_team_query(self) -> Query:
        """Build a query for Teams with matches in selected timespace."""
        return Query(Team).join(Team.seasons, Team.match_participations, MatchParticipation.match, Match.group).filter(Match.is_finished, self.build_filters())

    def build_match_query(self) -> Query:
        """Build a query for Matches in selected timespace."""
        return Query(Match).join(Match.group, Group.season).filter(Match.is_finished, self.build_filters())
