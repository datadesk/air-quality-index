import click
from air_quality_index import get_air_quality


@click.group()
def cmd():
    """
    A command-line interface for downloading air quality index data from AirNow.
    Returns GeoJSON.
    """
    pass


@cmd.command(help="Perimeters of active fires in a recent 24-hour period from GeoMAC")
def air_quality():
    click.echo(get_air_quality())


if __name__ == '__main__':
    cmd()
