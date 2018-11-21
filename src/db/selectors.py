from sqlalchemy import and_, or_

from .models import *


__all__ = (
    "matches_in_range",
)


def matches_in_year(session, year):
    return session.query(Match).filter(Season.year == year)


def matches_in_group(session, group):
    return session.query(Match).filter(Group.order_id == group)


def matches_in_years(session, lower_year, upper_year):
    return session.query(Match).filter(and_(Season.year >= lower_year, Season.year <= upper_year))


def matches_in_groups(session, lower_group, upper_group):
    return session.query(Match).filter(and_(Group.order_id >= lower_group, Group.order_id <= upper_group))


def matches_in_range(session, *, years=None, groups=None):
    if years is None and groups is None:
        return session.query(Match).all()
    elif years is None and groups is not None or years == (None, None):
        return matches_in_groups(session, *groups)
    elif years is not None and groups is None or groups == (None, None):
        return matches_in_years(session, *years)
    else:
        lower_year, upper_year = years
        lower_group, upper_group = groups
        return session.query(Match).filter(or_(
            and_(
                Group.season.year == lower_year,
                Group.order_id >= lower_group
            ),
            and_(
                Group.season.year > lower_year,
                Group.season.year < upper_year
            ),
            and_(
                Group.season.year == upper_year,
                Group.order_id <= upper_group
            )
        ))