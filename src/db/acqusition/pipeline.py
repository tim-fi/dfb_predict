from dateutil.parser import parse as parse_datetime
import requests

from ..db.models import Match, Team, Result, Season
from .core import Pipeline, Transformations


__all__ = (
    "pipeline",
    "download_matches"
)


pipeline = Pipeline({
    Team: {
        "id": Transformations.Get("TeamId"),
        "name": Transformations.Get("TeamName")
    },
    Result: {
        "id": Transformations.Get("ResultID"),
        "host_points": Transformations.Get("PointsTeam1"),
        "guest_points": Transformations.Get("PointsTeam2"),
        "is_end": Transformations.Get("ResultName") | Transformations.Custom(lambda data: "end" in data.lower())
    },
    Match: {
        "id": Transformations.Get("MatchID"),
        "date": Transformations.Get("MatchDateTime") | Transformations.Custom(lambda data: parse_datetime(data)),
        "host": Transformations.Get("Team1") | Transformations.GetOrCreate(Team),
        "guest": Transformations.Get("Team2") | Transformations.GetOrCreate(Team),
        "half_time_result": Transformations.Get("MatchResults") | Transformations.Filter(lambda item: item["ResultOrderID"] == 1) | Transformations.Get(0) | Transformations.Create(Result),
        "end_result": Transformations.Get("MatchResults") | Transformations.Filter(lambda item: item["ResultOrderID"] == 2) | Transformations.Get(0) | Transformations.Create(Result)
    }
})


base_url = "https://www.openligadb.de/api/getmatchdata/{league}/{year}"


def download_matches(session, years, league=None):
    for year in years:
        season = Season(year=year)

        url = base_url.format(league=league or "bl1", year=year)

        response = requests.get(url)
        data = response.json()

        for match in pipeline.create_multiple(Match, data, session):
            match.season = season

            if season not in match.host.seasons:
                match.host.seasons.append(season)

            if season not in match.guest.seasons:
                match.guest.seasons.append(season)

            yield match
