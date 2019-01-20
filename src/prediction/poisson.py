from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import numpy as np
from scipy.stats import poisson
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sqlalchemy.orm import Session

from ..db import RangeSelector
from .base import Model, PredictionResult


__all__ = (
    "PoissonModel",
    "PoissonResult"
)


@dataclass(frozen=True)
class PoissonResult(PredictionResult):
    goal_distribution: np.ndarray

    def __str__(self):
        if self.host_win:
            _goal_distribution = np.tril(self.goal_distribution, -1)
        elif self.guest_win:
            _goal_distribution = np.triu(self.goal_distribution, 1)
        elif self.draw:
            _goal_distribution = np.diag(self.goal_distribution)
        else:
            raise RuntimeError(f"Something magically stupid happen...")

        max_propbaility = _goal_distribution.argmax()
        host_goals, guest_goals = np.unravel_index(
            max_propbaility,
            _goal_distribution.shape
        )

        return super().__str__() + "\n".join([
            "",
            f" -> Most propable result: {host_goals}:{guest_goals} [{self.goal_distribution[host_goals,guest_goals]:.2%}]",
            *([
                " <!> A different result has a higher",
                "     propabilty but it lies outside",
                "     of the resultspace definied by",
                "     the most propable outcome.",
                "----------------------------------------",
            ] if max_propbaility != self.goal_distribution.argmax() else [
                "----------------------------------------"
            ])
        ])


class PoissonModel(Model, verbose_name="poisson"):
    """Poisson Regression

    This model uses Poisson Regression via an adapted implementation of
    https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling/.
    There are a few edge cases which can't properley be represented with this
    model though:
    1. If the selected source data only contains 1 group for each
       season, a perfect seperation error will pop up.
    2. If the selected source data is to sparse, i.e. only 5 groups
       per season, the predictions will be unreliable.

    """
    @staticmethod
    def calculate_model(selector: RangeSelector, session: Session):
        dfs = [
            {
                "host": match.host.shortname,
                "guest": match.guest.shortname,
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

        features = smf.glm(
            formula="goals ~ home + team + opponent",
            data=goal_model,
            family=sm.families.Poisson()
        ).fit()

        return features, list(goal_data["host"].unique())


    def make_prediction(self, host_name: str, guest_name: str, max_goals: int = 10) -> PoissonResult:
        host_goals_avg = self.features.predict(
            pd.DataFrame(data={
                "team": host_name,
                "opponent": guest_name,
                "home": 1
            }, index=[1])
        ).values[0]
        guest_goals_avg = self.features.predict(
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

        return PoissonResult(
            host_name=host_name,
            guest_name=guest_name,
            host_win_propability=np.sum(np.tril(results, -1)),
            draw_propability=np.sum(np.diag(results)),
            guest_win_propability=np.sum(np.triu(results, 1)),
            goal_distribution=results
        )
