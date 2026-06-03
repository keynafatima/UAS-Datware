import os
import click
from . import etl


@click.group()
def cli():
    pass


@cli.command()
def profile():
    """Profile CSV files in /data and print schema summary."""
    data_dir = os.getenv('DATA_DIR', '/data')
    etl.profile_data(data_dir)


@cli.command()
def run():
    """Run full ETL: create schema, load staging, and run basic transforms."""
    db = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'dw_user'),
        'password': os.getenv('DB_PASS', 'dw_pass'),
        'db': os.getenv('DB_NAME', 'dw'),
    }
    data_dir = os.getenv('DATA_DIR', '/data')
    etl.run_etl(db, data_dir)


if __name__ == '__main__':
    cli()
