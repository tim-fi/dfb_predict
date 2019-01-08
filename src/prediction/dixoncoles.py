from dataclasses import dataclass

import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..db import RangeSelector, Match
from .base import Predictor
from .poisson import PoissonResult


__all__ = (
    "DixonColesPredictor",
)


class DixonColesPredictor(Predictor, verbose_name="dixon-coles"):
    def calculate_model(self, selector: RangeSelector, session: Session) -> None:
        (max_date,) = session.query(func.max(Match.date)).filter(selector.build_filters()).first()
        dfs = [
            {
                "host": match.host.name,
                "guest": match.guest.name,
                "host_goals": match.host_points,
                "guest_goals": match.guest_points,
                "time_diff": (max_date - match.date).days,
            }
            for match in selector.build_match_query().with_session(session)
        ]
        if len(dfs) == 0:
            raise RuntimeError("Couldn't rebuild model, no matches for given selector...")
        goal_data = pd.DataFrame(dfs)

        team_query = selector.build_team_query().with_session(session)
        num_of_teams = team_query.count()
        teams = [team.name for team in team_query]

        init_vals = np.concatenate((
            np.random.uniform(0, 1, num_of_teams),
            np.random.uniform(0, -1, num_of_teams),
            np.array([0, 1.0])
        ))

        def estimate_params(params):
            attack_coeficients = dict(zip(teams, params[:num_of_teams]))
            defence_coeficients = dict(zip(teams, params[num_of_teams:-2]))
            rho, gamma = params[-2:]

            log_likelyhood = [
                self.dc_log_like_decay(
                    row.host_goals, row.guest_goals,
                    attack_coeficients[row.host], defence_coeficients[row.host],
                    attack_coeficients[row.guest], defence_coeficients[row.guest],
                    rho, gamma, row.time_diff, xi=0.001
                )
                for row in goal_data.itertuples()
            ]

            return -sum(log_likelyhood)

        min_result = minimize(
            estimate_params,
            init_vals,
            options={
                'disp': True,
                'maxiter': 10,
            },
            constraints=[{
                'type': 'eq',
                'fun': lambda x: sum(x[:20]) - 20
            }]
        )

        self._features = dict(zip(
            [f"attack_{team}" for team in teams] +
            [f"defence_{team}" for team in teams] +
            ['rho', 'home_advantage'],
            min_result.x
        ))

    def make_prediction(self, host_name: str, guest_name: str, max_goals: int = 10) -> PoissonResult:
        team_avgs = [
            np.exp(self._features[f"attack_{host_name}"] + self._features[f"defence_{guest_name}"] + self._features["home_advantage"]),
            np.exp(self._features[f"attack_{guest_name}"] + self._features[f"defence_{host_name}"])
        ]

        output_matrix = np.outer(*[
            np.array([
                poisson.pmf(i, team_avg)
                for i in range(1, max_goals + 1)
            ])
            for team_avg in team_avgs
        ])

        correction_matrix = np.array([
            [
                self.rho_correction(host_goals, guest_goals, team_avgs[0], team_avgs[1], self._features['rho'])
                for guest_goals in range(2)
            ]
            for host_goals in range(2)
        ])

        output_matrix[:2, :2] = output_matrix[:2, :2] * correction_matrix

        return PoissonResult(
            host_name=host_name,
            guest_name=guest_name,
            host_win_propability=np.sum(np.tril(output_matrix, -1)),
            draw_propability=np.sum(np.diag(output_matrix)),
            guest_win_propability=np.sum(np.triu(output_matrix, 1)),
            goal_distribution=output_matrix
        )

    @staticmethod
    def rho_correction(x, y, lambda_x, mu_y, rho):
        if x == 0 and y == 0:
            return 1 - (lambda_x * mu_y * rho)
        elif x == 0 and y == 1:
            return 1 + (lambda_x * rho)
        elif x == 1 and y == 0:
            return 1 + (mu_y * rho)
        elif x == 1 and y == 1:
            return 1 - rho
        else:
            return 1.0

    @staticmethod
    def dc_log_like_decay(x, y, alpha_x, beta_x, alpha_y, beta_y, rho, gamma, t, xi=0):
        print(x, alpha_x, beta_x)
        print(y, alpha_y, beta_y)
        print(rho, gamma, t, xi)
        lambda_x = np.exp(alpha_x + beta_y + gamma)
        mu_y = np.exp(alpha_y + beta_x)
        return (
            np.exp(-xi * t) *
            (
                np.log(DixonColesPredictor.rho_correction(x, y, lambda_x, mu_y, rho)) +
                np.log(poisson.pmf(x, lambda_x)) +
                np.log(poisson.pmf(y, mu_y))
            )
        )
