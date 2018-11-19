import unittest

from ..db.core import _DB
from ..db.models import *  # noqa: 401
from ..acquisition import download_matches, clean_download_list


class _DummyYear(int):
    ...


class TestAcquisition(unittest.TestCase):
    def setUp(self):
        self.DB = _DB("sqlite:///:memory:")
        self.DB.create_tables()

    def download(self, years):
        """Assert riddled variant of the cli download method

        :param years: years to download

        """
        with self.DB.get_session() as session:
            dummy_year = _DummyYear(0)
            years_to_download, existing_years = clean_download_list(session, [dummy_year] + years)
            assert dummy_year in years_to_download
            assert all(year not in existing_years for year in years_to_download)
            years_to_download = [year for year in years_to_download if not isinstance(year, _DummyYear)]

            tally = 0
            for match in download_matches(session, years_to_download):
                if tally % 306 == 0:
                    target_year = years_to_download[tally // 306]
                self._test_match(match, target_year)
                tally += 1
                session.add(match)
            assert tally == len(years_to_download) * 306

    def _test_match(self, match, year=None):
        """Check a given match for validity

        :param match: object to check
        :param year: year to use for comparisons (default value = None)
        
        """
        assert isinstance(match, Match)
        assert isinstance(match.season, Season)
        if year is not None:
            assert match.season.year == year
        self._test_team(match.host, year)
        self._test_team(match.guest, year)
        assert isinstance(match.half_time_result, Result)
        assert isinstance(match.end_result, Result)

    def _test_team(self, team, year=None):
        """Check a given team for validity

        :param match: object to check
        :param year: year to use for comparisons (default value = None)
        
        """
        assert isinstance(team, Team)
        assert isinstance(team.seasons, list)
        assert all(isinstance(season, Season) for season in team.seasons)
        if year is not None:
            assert any(season.year == year for season in team.seasons)

    def test_aqcuisition(self):
        """Test the acquisition of a single year."""
        self.download([2016])

    def test_aqcuisition_multiple(self):
        """Test the acquisition of multiple years."""
        self.download([2015, 2017])

    def test_aqcuisition_with_collision(self):
        """Test the acquisition for collisions."""
        self.download([2015, 2016, 2017])
