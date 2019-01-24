import unittest

from ..db.core import _DB
from ..db.selectors import RangeSelector, RangePoint
from ..db.models import *  # noqa: 401
from ..acquisition import download_matches
from ..prediction import PoissonModel, DixonColesModel


class TestPrediction(unittest.TestCase):
    """Testcases for the predictions."""
    def setUp(self):
        self.DB = _DB("sqlite:///:memory:")
        self.DB.drop_tables()
        self.DB.create_tables()
        with self.DB.get_session() as session:
            session.add_all(list(download_matches(session, [2016])))

    def test_poisson(self):
        """>>> Test the Poisson Regression prediction method."""
        with self.DB.get_session() as session:
            model = PoissonModel(RangeSelector(), session)
        result_obj = model.make_prediction("FCB", "BVB")

        assert all(
            round(actual, 2) == expected
            for actual, expected in zip(
                (result_obj.host_win_propability, result_obj.draw_propability, result_obj.guest_win_propability),
                (0.73, 0.16, 0.11)
            )
        ), f"Result wasn't what we expected... {result} != {expected_result}"

    def test_dixoncoles(self):
        """>>> Test the Dixon-Coles prediction method."""
        with self.DB.get_session() as session:
            model = DixonColesModel(RangeSelector(
                RangePoint(2016, 30), RangePoint(2016, 34)
            ), session)
        result_obj = model.make_prediction("FCB", "BVB")

        assert result_obj is not None, "Result didn't compute..."
