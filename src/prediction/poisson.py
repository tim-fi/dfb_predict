import pandas as pd
import numpy as np
from scipy.stats import poisson
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sqlalchemy.orm import Session

from ..db import RangeSelector
from .base import Predictor


__all__ = (
    "PoissonPredictor",
)


class PoissonPredictor(Predictor, verbose_name="poisson"):
    def __init__(self) -> None:
        self._model = None

    def calculate_model(self, selector: RangeSelector, session: Session) -> None:
        dfs = [
            {
                "host": match.host.name,
                "guest": match.guest.name,
                "host_goals": match.host_points,
                "guest_goals": match.guest_points,
            }
            for match in selector.build_match_query().with_session(session)
        ]
        if len(dfs) == 0:
            raise RuntimeError("Couldn't rebuild model, no matches for given selector...")
        goal_data = pd.DataFrame(dfs)

        # Here the model for the goals is created,
        # the resulting dataframe follows the form:
        # <team> | <opponent> | <goals> | <home>
        # --------------------------------------
        # team:     represents the team to which the goal count belongs
        # opponent: represents the opponent <team> faced in the match
        # goals:    simply the goal count
        # home:     1|0 where 1 represents that the team
        #           hosted the match and 0 the opposite
        # --------------------------------------
        goal_model = pd.concat([
            goal_data[["host", "guest", "host_goals"]].assign(home=1).rename(
                columns={
                    "host": "team",
                    "guest": "opponent",
                    "host_goals": "goals"
                }
            ),
            goal_data[["host", "guest", "guest_goals"]].assign(home=0).rename(
                columns={
                    "guest": "team",
                    "host": "opponent",
                    "guest_goals": "goals"
                }
            ),
        ], sort=False)

        self._model = smf.glm(
            formula="goals ~ home + team + opponent",
            data=goal_model,
            family=sm.families.Poisson()
        ).fit()

    def make_prediction(self, host_name, guest_name, max_goals=10):
        host_goals_avg = self._model.predict(
            pd.DataFrame(data={
                "team": host_name,
                "opponent": guest_name,
                "home": 1
            }, index=[1])
        ).values[0]
        guest_goals_avg = self._model.predict(
            pd.DataFrame(data={
                "team": guest_name,
                "opponent": host_name,
                "home": 0
            }, index=[1])
        ).values[0]

        prediction = [
            [
                poisson.pmf(i, goal_avg)
                for i in range(max_goals + 1)
            ]
            for goal_avg in [host_goals_avg, guest_goals_avg]
        ]

        results = np.outer(
            np.array(prediction[0]),
            np.array(prediction[1])
        )

        return {
            "host": np.sum(np.tril(results, -1)),
            "draw": np.sum(np.diag(results)),
            "guest": np.sum(np.triu(results, 1))
        }
