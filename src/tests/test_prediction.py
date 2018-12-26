import unittest

from ..db.core import _DB
from ..db.selectors import RangeSelector
from ..db.models import *  # noqa: 401
from ..acquisition import download_matches
from ..prediction import PoissonPredictor


class TestPrediction(unittest.TestCase):
    """Testcases for the predictions."""
    def setUp(self):
        self.DB = _DB("sqlite:///:memory:")
        self.DB.drop_tables()
        self.DB.create_tables()
        with self.DB.get_session() as session:
            session.add_all(list(download_matches(session, [2016])))

    def test_poisson(self):
        """>>> Test the poisson prediction algorithm."""
        p = PoissonPredictor()
        with self.DB.get_session() as session:
            p.calculate_model(RangeSelector(), session)
        result_obj = p.make_prediction("FC Bayern", "Borussia Dortmund")

        assert all(
            round(actual, 2) == expected
            for actual, expected in zip(
                (result_obj.host_win_propability, result_obj.draw_propability, result_obj.guest_win_propability),
                (0.73, 0.16, 0.11)
            )
        ), f"Result wasn't what we expected... {result} != {expected_result}"
