from __future__ import annotations
from typing import Dict
import json

import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import RangeSelector, Match
from .base import Model
from .poisson import PoissonResult


__all__ = (
    "DixonColesModel",
)


class DixonColesModel(Model, verbose_name="dixon-coles"):
    @staticmethod
    def calculate_model(selector: RangeSelector, session: Session) -> Dict[str, float]:
        team_query = selector.build_team_query().with_session(session)
        num_of_teams = team_query.count()
        teams = [team.shortname for team in team_query]

        (max_date,) = session.query(func.max(Match.date)).filter(selector.build_filters()).first()
        dfs = [
            {
                "host": teams.index(match.host.shortname),
                "guest": teams.index(match.guest.shortname),
                "host_goals": match.host_points,
                "guest_goals": match.guest_points,
                "time_diff": np.exp((max_date - match.date).days * 0.001),
            }
            for match in selector.build_match_query().with_session(session)
        ]
        if len(dfs) == 0:
            raise RuntimeError("Couldn't rebuild model, no matches for given selector...")
        matches = pd.DataFrame(dfs)

        def estimate_params(params):
            attack = params[:num_of_teams]
            defence = params[num_of_teams:-2]
            score_correction, home_advantage = params[-2:]
            return -1 * np.sum(
                matches["time_diff"] *  # noqa: W504
                log_likelyhood(
                    matches["host_goals"], matches["guest_goals"],
                    np.exp(attack[matches["host"]] + defence[matches["guest"]] + home_advantage),
                    np.exp(attack[matches["guest"]] + defence[matches["guest"]]),
                    score_correction
                )
            )

        min_result = minimize(
            estimate_params,
            np.array(
                [.01] * num_of_teams +  # noqa: W504
                [-0.08] * num_of_teams +  # noqa: W504
                [0.03, 0.06]
            ),
            options={
                # 'disp': True,
                'maxiter': 100,
            },
            constraints=[{
                'type': 'eq',
                'fun': lambda x: sum(x[:18]) - 18
            }]
        )

        features = dict(zip(
            ["attack_" + team for team in teams] +
            ["defence_" + team for team in teams] +
            ['score_correction', 'home_advantage'],
            min_result.x
        ))

        return features, teams

    def make_prediction(self, host_name: str, guest_name: str, max_goals: int = 10) -> PoissonResult:
        team_avgs = [
            np.exp(self.features[f"attack_{host_name}"] + self.features[f"defence_{guest_name}"] + self.features["home_advantage"]),
            np.exp(self.features[f"attack_{guest_name}"] + self.features[f"defence_{host_name}"]),
        ]

        output_matrix = np.outer(*[
            np.array([poisson.pmf(i, team_avg) for i in range(0, max_goals + 1)])
            for team_avg in team_avgs
        ])

        correction_matrix = np.array([
            [
                apply_score_correction(host_goals, guest_goals, team_avgs[0], team_avgs[1], self.features['score_correction'])
                for guest_goals in range(2)
            ]
            for host_goals in range(2)
        ])

        output_matrix[:2, :2] = output_matrix[:2, :2] * correction_matrix

        return PoissonResult(
            model_type=type(self).verbose_name,
            host_name=host_name,
            guest_name=guest_name,
            host_win_propability=np.sum(np.tril(output_matrix, -1)),
            draw_propability=np.sum(np.diag(output_matrix)),
            guest_win_propability=np.sum(np.triu(output_matrix, 1)),
            goal_distribution=output_matrix
        )


def apply_score_correction(host_goals, guest_goals, host_bias, guest_bias, score_correction):
    if host_goals == 0 and guest_goals == 0:
        return 1 - (host_bias * guest_bias * score_correction)
    elif host_goals == 0 and guest_goals == 1:
        return 1 + (host_bias * score_correction)
    elif host_goals == 1 and guest_goals == 0:
        return 1 + (guest_bias * score_correction)
    elif host_goals == 1 and guest_goals == 1:
        return 1 - score_correction
    else:
        return 1.0


apply_score_correction_vec = np.vectorize(apply_score_correction)


def log_likelyhood(host_goals, guest_goals, host_bias, guest_bias, score_correction):
    return (
        np.log(apply_score_correction_vec(host_goals, guest_goals, host_bias, guest_bias, score_correction)) +  # noqa: W504
        np.log(poisson.pmf(host_goals, host_bias)) +  # noqa: W504
        np.log(poisson.pmf(guest_goals, guest_bias))
    )
