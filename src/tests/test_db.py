import unittest

from sqlalchemy.orm import Session

from ..db.core import _DB
from ..db.models import *  # noqa: F401


class TestDB(unittest.TestCase):
    def setUp(self):
        self.DB = _DB("sqlite:///:memory:")
        self.DB.create_tables()

    def test_get_session(self):
        """>>> Test the session functionality of our DB-wrapper-class."""
        with self.DB.get_session() as session:
            assert isinstance(session, Session)
