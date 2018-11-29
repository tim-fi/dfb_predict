import click

from sqlalchemy import or_

from .db import DB
from .db.models import *  # noqa: F401
from .db.selectors import RangePoint, RangeSelector
from .prediction import PREDICTOR_CLASS_REGISTRY
from .acquisition import download_matches, clean_download_list


@click.group()
def cli():
    ...


@cli.group()
def db():
    ...


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
@click.option("-p", "--predictor", type=click.Choice(PREDICTOR_CLASS_REGISTRY.keys()), default=list(PREDICTOR_CLASS_REGISTRY.keys())[0], help="The predictor to use.")
def predict(host, guest, predictor):
    """Make prediction for two given teams."""
    predictor = PREDICTOR_CLASS_REGISTRY[predictor]()
    with DB.get_session() as session:
        predictor.calculate_model(RangeSelector(), session)
        host_id = session.query(Team.id).filter(or_(Team.name.contains(host), Team.name.ilike(host))).first()
        guest_id = session.query(Team.id).filter(or_(Team.name.contains(guest), Team.name.ilike(guest))).first()
        print(predictor.make_prediction(host_id, guest_id))


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
        print(*selector.build_query().with_session(session), sep="\n")


@query.command()
def teams():
    with DB.get_session() as session:
        print(*session.query(Team).all(), sep="\n")
