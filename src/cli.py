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
def predict(host, guest, predictor):
    """Make prediction for two given teams."""
    predictor = Predictor.registry[predictor]()
    with DB.get_session() as session:
        predictor.calculate_model(RangeSelector(), session)
        host_candidates = session.query(Team).filter(or_(Team.name.contains(host), Team.name.ilike(host)))
        guest_candidates = session.query(Team).filter(or_(Team.name.contains(guest), Team.name.ilike(guest)))

        errors = []
        if host_candidates.count() > 1:
            errors.append(f"Multiple options for {repr(host)}: {', '.join(str(team) for team in host_candidates)}")
        if guest_candidates.count() > 1:
            errors.append(f"Multiple options for {repr(guest)}: {', '.join(str(team) for team in guest_candidates)}")
        if host_candidates.count() == 0:
            errors.append(f"Couldn't find team for {repr(host)}.")
        if guest_candidates.count() == 0:
            errors.append(f"Couldn't find team for {repr(guest)}.")
        if len(errors) > 0:
            for error in errors:
                print("ERR:", error)
            print("\nOptions for teams:")
            print(*["> " + str(team) for team in session.query(Team).all()], sep="\n")
        else:
            host_name = host_candidates.first().name
            guest_name = guest_candidates.first().name
            print(host_name, "vs", guest_name)
            print(predictor.make_prediction(host_name, guest_name))


@db.group()
def query():
    ...


@query.command()
def matches():
    selector = RangeSelector(
        start=RangePoint(),
        end=RangePoint()
    )
    with DB.get_session() as session:
        print(*selector.build_match_query().with_session(session), sep="\n")


@query.command()
def teams():
    with DB.get_session() as session:
        print(*session.query(Team).all(), sep="\n")
