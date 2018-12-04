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
            result = p.make_prediction("FC Bayern", "Borussia Dortmund")
            expected_result = {'host': 0.7330641802459998, 'draw': 0.16066711952653115, 'guest': 0.10621035363363719}

            assert result == expected_result, "Result wasn't what we expected..."
            # This check incorperates all of the following:
            # 0. assert len(result) == len(expected_result), "Result has wrong length"
            # 1. assert len(set(result.keys()) - set(expected_result.keys())) == 0, "Unexpect result keys"
            # 2. assert len(set(result.values()) - set(expected_result.values())) == 0, "Unexpected result values"
            # 3. assert result["host"] == expected_result["host"], "Wrong value for host_win"
            # 4. assert result["draw"] == expected_result["draw"], "Wrong value for draw"
            # 5. assert result["guest"] == expected_result["guest"], "Wrong value for guest_win"
