from typing import List, Optional, Generator, cast

from dateutil.parser import parse as parse_datetime
import requests
from sqlalchemy.orm import Session

from ..db import Model
from ..db.models import Match, Team, Result, Season
from .core import Pipeline
from .transformations import Get, Custom, Filter, GetOrCreate, Create


__all__ = (
    "pipeline",
    "download_matches"
)


pipeline: Pipeline[Model] = Pipeline({
    Team: {
        "id": Get("TeamId"),
        "name": Get("TeamName")
    },
    Result: {
        "id": Get("ResultID"),
        "host_points": Get("PointsTeam1"),
        "guest_points": Get("PointsTeam2"),
        "is_end": Get("ResultName") | Custom(lambda data: "end" in data.lower())
    },
    Match: {
        "id": Get("MatchID"),
        "date": Get("MatchDateTime") | Custom(lambda data: parse_datetime(data)),
        "host": Get("Team1") | GetOrCreate(Team),
        "guest": Get("Team2") | GetOrCreate(Team),
        "half_time_result": Get("MatchResults") | Filter(lambda item: item["ResultOrderID"] == 1) | Get(0) | Create(Result),
        "end_result": Get("MatchResults") | Filter(lambda item: item["ResultOrderID"] == 2) | Get(0) | Create(Result)
    }
})


base_url = "https://www.openligadb.de/api/getmatchdata/{league}/{year}"


def download_matches(session: Session, years: List[int], league: Optional[str] = None) -> Generator[Match, None, None]:
    """Download and process all matches from the given years

    :param session: DB session to interact with
    :param years: list of year to download matches of
    :param league: key od league to download matches of (default value = None)

    """
    for year in years:
        season = Season(year=year)  # type: ignore

        url = base_url.format(league=league or "bl1", year=year)

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for match in pipeline.create_multiple(Match, data, session):  # type: ignore
            match = cast(Match, match)  # this cast is required for "proper typing2...i.e. typevars are annoying
            match.season = season

            if season not in match.host.seasons:
                match.host.seasons.append(season)

            if season not in match.guest.seasons:
                match.guest.seasons.append(season)

            yield match
