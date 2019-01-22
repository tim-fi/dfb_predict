from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Generator, cast, Tuple, Dict, Any

from dateutil.parser import parse as parse_datetime
import requests
from sqlalchemy.orm import Session

from ..db import Model
from ..db.models import Match, Team, Season, Group, MatchParticipation
from .core import Pipeline
from .transformations import Get, Custom, Filter, GetOrCreate, CreateMultiple, If, Constant


__all__ = (
    "pipeline",
    "download_matches",
    "clean_download_list",
    "get_current_groups_matches"
)


pipeline: Pipeline[Model] = Pipeline({
    MatchParticipation: {
        "team": Get("Team") | GetOrCreate(Team, match_targets=["id"]),
        "match_id": Get("MatchID"),
        "hosted": Get("hosted"),
    },
    Team: {
        "id": Get("TeamId"),
        "name": If(
            cond=lambda data: "ShortName" in data and data["ShortName"],
            then=Get("ShortName"),
            else_=Get("TeamName"),
        )
    },
    Group: {
        "id": Get("GroupID"),
        "order_id": Get("GroupOrderID"),
    },
    Match: {
        "id": Get("MatchID"),
        "date": Get("MatchDateTime") | Custom(lambda data: parse_datetime(data)),
        "is_finished": Get("MatchIsFinished"),
        "group": Get("Group") | GetOrCreate(Group, match_targets=["id"]),
        "match_participations": Custom(lambda data: [
            {"MatchID": data["MatchID"], "Team": data["Team1"], "hosted": True},
            {"MatchID": data["MatchID"], "Team": data["Team2"], "hosted": False},
        ]) | CreateMultiple(MatchParticipation),
        "host_points": Get("MatchResults") | Filter(lambda item: "end" in item["ResultName"].lower()) | If(
            cond=lambda data: len(data) > 0,
            then=Get(0) | Get("PointsTeam1"),
            else_=Constant(0)
        ),
        "guest_points": Get("MatchResults") | Filter(lambda item: "end" in item["ResultName"].lower()) | If(
            cond=lambda data: len(data) > 0,
            then=Get(0) | Get("PointsTeam2"),
            else_=Constant(0)
        ),
    }
})


def clean_download_list(session: Session, years: List[int]) -> Tuple[List[int], List[int]]:
    """Check if a given list of years for possible duplicates with existing years.

    :param session: DB session to interact with
    :param years: years to check for duplicates
    :return: (unique years, duplicates years)

    """
    existing_years = [year for (year,) in session.query(Season.year).all()]
    skipped_years = [year for year in years if year in existing_years]
    years_to_download = [year for year in years if year not in existing_years]

    return years_to_download, skipped_years


base_url = "https://www.openligadb.de/api/getmatchdata/{league}/{year}"


def _download_matches(years: List[int], league: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """Download all matches from the given years

    This is a "private" method, which does the job of actually downloading the data.
    To make this fast we use a ThreadPoolExecutor, as the actual sending of the request
    is blocking which can easily be done in parallel.

    :param years: list of year to download matches of
    :param league: key od league to download matches of (default value = None)

    """
    def download_job(year):
        url = base_url.format(league=league or "bl1", year=year)
        return year, requests.get(url)

    with ThreadPoolExecutor(max_workers=len(years)) as executor:
        downloads = [executor.submit(download_job, year) for year in years]
        for future in as_completed(downloads):
            year, response = future.result()
            response.raise_for_status()
            yield year, response.json()


def download_matches(session: Session, years: List[int], league: Optional[str] = None) -> Generator[Match, None, None]:
    """Download and process all matches from the given years

    :param session: DB session to interact with
    :param years: list of year to download matches of
    :param league: key od league to download matches of (default value = None)

    """
    for year, data in _download_matches(years, league):
        season = Season(year=year)  # type: ignore

        for match in pipeline.create_multiple(Match, data, session):  # type: ignore
            match = cast(Match, match)  # this cast is required for "proper typing2...i.e. typevars are annoying
            match.group.season = season

            if season not in match.host.seasons:
                match.host.seasons.append(season)

            if season not in match.guest.seasons:
                match.guest.seasons.append(season)

            yield match


def get_current_groups_matches() -> List[Tuple[str, str]]:
    """Get the matches of the current group"""
    response = requests.get("https://www.openligadb.de/api/getmatchdata/bl1")
    response.raise_for_status()
    data = response.json()
    return (
        data[0]["LeagueName"],
        data[0]["Group"]["GroupOrderID"],
        [
            (
                match["Team1"].get("ShortName") or match["Team1"]["TeamName"],
                match["Team2"].get("ShortName") or match["Team2"]["TeamName"])
            for match in data
        ]
    )
