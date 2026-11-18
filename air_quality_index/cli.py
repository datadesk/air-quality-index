"""The airqualityindex command-line interface."""

from __future__ import annotations

import click

from air_quality_index import AirNowError, get_air_quality
from air_quality_index.fetch import DEFAULT_TIMEOUT


@click.group()
def cmd() -> None:
    """A command-line interface for downloading PM2.5 air quality index data from AirNow."""
    pass


@cmd.command(help="Download latest air quality GeoJSON data")
@click.option(
    "--timeout",
    default=DEFAULT_TIMEOUT,
    show_default=True,
    type=click.FloatRange(min=1),
    help="Seconds to wait for AirNow on each try",
)
@click.option("--verbose", is_flag=True, help="Print each request to stderr")
@click.option(
    "--repair/--no-repair",
    default=True,
    show_default=True,
    help="Repair invalid shapes, or keep them exactly as AirNow wrote them",
)
def air_quality(timeout: float, verbose: bool, repair: bool) -> None:
    """Print AirNow's current PM2.5 map as GeoJSON.

    Args:
        timeout: Seconds to wait for AirNow on each try.
        verbose: Whether to print each request to standard error.
        repair: Whether to repair invalid shapes.

    Raises:
        click.ClickException: If AirNow cannot be reached or sends back an
            error, so the command prints one line starting with "Error:" and
            exits with code 1.
    """
    try:
        data = get_air_quality(verbose=verbose, timeout=timeout, repair=repair)
    except AirNowError as error:
        raise click.ClickException(str(error)) from error
    click.echo(data)


if __name__ == "__main__":
    cmd()
