from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, DateTime, ForeignKey, String, or_, Boolean, Table
from sqlalchemy.orm import relationship, sessionmaker, scoped_session


__all__ = (
    "get_session",
    "Season",
    "Match",
    "Results",
    "Team"
)


engine = create_engine("sqlite:///:memory:")
base = declarative_base(bind=engine)

class Season(base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)

    year = Column(Integer)

    teams = relationship("Team", secondary=team_season_association_table, back_populates="seasons")


class Match(base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, unique=True)

    date = Column(DateTime)

    season_id = Column(Integer, ForeignKey("seasons.id"))
    season = relationship("Season", backref="matches")

    host_id = Column(Integer, ForeignKey("teams.id"))
    host = relationship("Team", backref="hosted_matches", primaryjoin=lambda: Match.host_id == Team.id)

    guest_id = Column(Integer, ForeignKey("teams.id"))
    guest = relationship("Team", backref="guest_matches", primaryjoin=lambda: Match.guest_id == Team.id)

    half_time_result_id = Column(Integer, ForeignKey("results.id"))
    half_time_result = relationship("Result", primaryjoin=lambda: Match.half_time_result_id == Result.id)
    
    end_result_id = Column(Integer, ForeignKey("results.id"))
    end_result = relationship("Result", primaryjoin=lambda: Match.end_result_id == Result.id)

    results = relationship("Result", backref="match", primaryjoin=lambda: or_(Match.end_result_id == Result.id, Match.half_time_result_id == Result.id))


class Result(base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, unique=True)

    host_points = Column(Integer)
    guest_points = Column(Integer)

    is_end = Column(Boolean)


class Team(base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, unique=True)

    name = Column(String)

    seasons = relationship("Season", secondary=team_season_association_table, back_populates="teams")

team_season_association_table = Table(
    "team_seasons_association", base.metadata,
    Column("season_id", Integer, ForeignKey("seasons.id")),
    Column("team_id", Integer, ForeignKey("teams.id")),
)

base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
ScopedSession = scoped_session(Session)

@contextmanager
def get_session(*args, scoped=False, **kwargs):
    session = Session(*args, **kwargs) if not scoped else ScopedSession(*args, **kwargs)
    try:
        yield session
    except:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()
