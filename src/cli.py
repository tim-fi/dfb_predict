import click

from .db import DB
from .db.models import *
from .acquisition import download_matches


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
        existing_years = [year for (year,) in session.query(Season.year).all()]
        skipped_years = [year for year in years if year in existing_years]
        years_to_download = [year for year in years if year not in existing_years]

        if len(years_to_download) == 0:
            print("All seasons already present, none will be downloaded.")
        elif len(skipped_years) > 0:
            print("Skipping ", ", ".join(map(str, skipped_years)), "as they are already present.")

        with click.progressbar(
            download_matches(session, years_to_download),
            length=len(years_to_download) * 306,
            label="downloading matches...",
            show_eta=True, show_percent=True, show_pos=True
        ) as result:
            session.add_all(list(result))
    print("done")
