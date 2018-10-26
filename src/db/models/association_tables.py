from sqlalchemy import Table, Integer, Column, ForeignKey

from ..core import DB


__all__ = (
    "team_season_association_table",
)


team_season_association_table = Table(
    "team_seasons_association", DB.Model.metadata,  # type: ignore
    Column("season_id", Integer, ForeignKey("seasons.id")),
    Column("team_id", Integer, ForeignKey("teams.id")),
)
