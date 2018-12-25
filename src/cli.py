import click

from sqlalchemy import or_

from .db import DB
from .db.models import *  # noqa: F401
from .db.selectors import RangePoint, RangeSelector
from .prediction import Predictor
from .acquisition import download_matches, clean_download_list, get_current_groups_matches
from .ui import App


@click.group()
def cli():
    ...


@cli.command()
def ui():
    App.run_app()


@cli.command()
def currentmatches():
    season_name, group_id, matches = get_current_groups_matches()
    print(
        f"Spiele am {group_id}-ten Spieltag der {season_name}: ",
        *[
            f"{i+1}: {host} vs {guest}"
            for i, (host, guest) in enumerate(matches)
        ],
        sep="\n"
    )


@cli.group()
def db():
    ...


@db.command()
@click.option("-y", "--yes", is_flag=True, help="skip confirmation prompt")
def drop(yes):
    if yes or click.confirm("Are you sure you want to drop all tables?", abort=True):
        if not yes:
            print("dropping tables...", end="")
        DB.drop_tables()
        DB.create_tables()
        if not yes:
            print("done")


@db.command()
@click.argument("years", nargs=-1, type=int)
@click.option("-d", "--drop", is_flag=True, help="drop all tables before downloading matches")
def download(years, drop):
    if drop and click.confirm("Are you sure you want to drop all tables?", abort=True):
        print("dropping tables...")
        DB.drop_tables()
        DB.create_tables()

    with DB.get_session() as session:
        years_to_download, skipped_years = clean_download_list(session, years)

        if len(years_to_download) == 0:
            print("All seasons already present, none will be downloaded.")
            return
        elif len(skipped_years) > 0:
            print("Skipping ", ", ".join(map(str, skipped_years)), f"as {'they are' if len(skipped_years) > 1 else 'it is'} already present.")

        with click.progressbar(
            download_matches(session, years_to_download),
            length=len(years_to_download) * 306,
            label="downloading matches...",
            show_eta=True, show_percent=True, show_pos=True
        ) as result:
            session.add_all(list(result))
    print("done")


@cli.command()
@click.argument("host", type=str, nargs=1)
@click.argument("guest", type=str, nargs=1)
@click.option("-p", "--predictor", type=click.Choice(Predictor.registry.keys()), default=list(Predictor.registry.keys())[0], help="The predictor to use.")
@click.option("-s", "--start", type=str, default=None, help="Lower time constraint of data. Format: <year>[/<group>]")
@click.option("-e", "--end", type=str, default=None, help="Upper time constraint of data. Format: <year>[/<group>]")
def predict(host, guest, predictor, start, end):
    """Make prediction for two given teams."""
    predictor = Predictor.registry[predictor]()
    with DB.get_session() as session:
        selector, errors = handle_selector(start, end, session)
        team_query = selector.build_team_query()
        host_candidates = list(team_query.filter(or_(Team.name.contains(host), Team.name.ilike(host))).with_session(session))
        guest_candidates = list(team_query.filter(or_(Team.name.contains(guest), Team.name.ilike(guest))).with_session(session))
        if len(host_candidates) > 1:
            errors.append(f"Multiple options for {repr(host)}: {', '.join(str(team) for team in host_candidates)}")
        if len(guest_candidates) > 1:
            errors.append(f"Multiple options for {repr(guest)}: {', '.join(str(team) for team in guest_candidates)}")
        if len(host_candidates) == 0:
            errors.append(f"Couldn't find team for {repr(host)}.")
        if len(guest_candidates) == 0:
            errors.append(f"Couldn't find team for {repr(guest)}.")
        if len(errors) > 0:
            for error in errors:
                print("ERR:", error)
            print(f"\nOptions for teams:")
            print(*["> " + str(team) for team in team_query.with_session(session)], sep="\n")
        else:
            predictor.calculate_model(RangeSelector(start, end), session)
            host_name = host_candidates[0].name
            guest_name = guest_candidates[0].name
            print(predictor.make_prediction(host_name, guest_name))


def handle_selector(start, end, session):
    start = RangePoint.parse_from_string(start)
    end = RangePoint.parse_from_string(end)

    errors = []
    if start.year is not None and session.query(Season).filter(Season.year >= start.year).count() < 1:
        errors.append(f"Couldn't find any year >= {start.year} in database.")
    if end.year is not None and session.query(Season).filter(Season.year <= end.year).count() < 1:
        errors.append(f"Couldn't find any year <= {end.year} in database.")
    if start.group is not None and start.group not in range(1, 35):
        errors.append(f"Group of lower bound must be in 1..34. Not {start.group}...")
    if end.group is not None and end.group not in range(1, 35):
        errors.append(f"Group of upper bound must be in 1..34. Not {end.group}...")
    return RangeSelector(start, end), errors


@db.group()
def query():
    ...


@query.command()
def seasons():
    with DB.get_session() as session:
        print("Downloaded seasons:", ", ".join(str(season.year) for season in session.query(Season).all()))


@query.command()
@click.option("-s", "--start", type=str, default=None, help="Lower time constraint of data. Format: <year>[/<group>]")
@click.option("-e", "--end", type=str, default=None, help="Upper time constraint of data. Format: <year>[/<group>]")
def matches(start, end):
    with DB.get_session() as session:
        selector, errors = handle_selector(start, end, session)
        if len(errors) > 0:
            for error in errors:
                print("ERR:", error)
        else:
            print(*selector.build_match_query().with_session(session), sep="\n")


@query.command()
@click.option("-s", "--start", type=str, default=None, help="Lower time constraint of data. Format: <year>[/<group>]")
@click.option("-e", "--end", type=str, default=None, help="Upper time constraint of data. Format: <year>[/<group>]")
def teams(start, end):
    with DB.get_session() as session:
        selector, errors = handle_selector(start, end, session)
        if len(errors) > 0:
            for error in errors:
                print("ERR:", error)
        else:
            print(*selector.build_team_query().with_session(session), sep="\n")
