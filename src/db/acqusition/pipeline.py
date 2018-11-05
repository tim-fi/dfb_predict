from dateutil.parser import parse as parse_datetime

from ..db.models import Match, Team, Result
from .core import Pipeline, Transformations


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

