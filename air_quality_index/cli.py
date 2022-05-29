import click
from air_quality_index import get_air_quality


@click.group()
def cmd():
    """A command-line interface for downloading air quality index data from AirNow."""
    pass


@cmd.command(help="Download latest air quality GeoJSON data")
def air_quality():
    click.echo(get_air_quality())


if __name__ == '__main__':
    cmd()
