"""Download air quality index data from AirNow."""

from __future__ import annotations

from geojson import Feature, FeatureCollection, MultiPolygon, Polygon

from .errors import AirNowDataError, AirNowError
from .fetch import DEFAULT_TIMEOUT, download_kml
from .kml import read_kml
from .records import AirQualityArea, AirQualityLevel, AirQualityReport

__all__ = [
    "AirNowDataError",
    "AirNowError",
    "AirQualityArea",
    "AirQualityLevel",
    "AirQualityReport",
    "get_air_quality",
    "get_air_quality_report",
]


def get_air_quality(
    verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> FeatureCollection:
    """
    Download PM2.5 air quality index data from AirNow.

    A download is tried up to four times, so a short AirNow outage does not stop
    it.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for AirNow on each try. Defaults to 30.

    Returns:
        A GeoJSON FeatureCollection. Each feature is a Polygon, with the
        coordinates written as [longitude, latitude, 0], whose properties are
        ``description`` (the HTML AirNow shows in its pop-up) and ``styleUrl``
        (the air quality level, such as "#Good" or "#Unhealthy").

    Raises:
        AirNowError: If AirNow cannot be reached or answers with an error.
        AirNowDataError: If the file arrives but cannot be read.

    Examples:
        >>> data = get_air_quality()
        >>> data = get_air_quality(timeout=60, verbose=True)
        >>> data["features"][0]["properties"]["styleUrl"]
        '#Good'
    """
    # Get it
    content = download_kml(verbose=verbose, timeout=timeout)

    # Read the KML. It is plain XML, so the standard library can do it.
    kml = read_kml(content)

    # Tidy it up
    feature_list = []
    for placemark in kml.placemarks:
        # Make a Polygon, or a MultiPolygon if AirNow ever sends several at once
        polygons = placemark.polygons
        if not polygons:
            continue
        geometry = (
            Polygon(polygons[0]) if len(polygons) == 1 else MultiPolygon(polygons)
        )
        feature_list.append(Feature(geometry=geometry, properties=placemark.properties))

    # Return the results
    return FeatureCollection(feature_list)


def get_air_quality_report(
    verbose: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> AirQualityReport:
    """
    Download PM2.5 air quality index data from AirNow as typed records.

    It reads the same file as ``get_air_quality``.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for AirNow on each try. Defaults to 30.

    Returns:
        An ``AirQualityReport`` with the hour the map is for, in UTC, and one
        ``AirQualityArea`` for each patch of the map.

    Raises:
        AirNowError: If AirNow cannot be reached or answers with an error.
        AirNowDataError: If the file has no date and hour, or a level this
            package does not know. It is also a ``ValueError``.

    Examples:
        >>> report = get_air_quality_report()
        >>> report.observed_at.tzinfo is not None
        True
        >>> report.areas[0].level.label
        'Good'
    """
    content = download_kml(verbose=verbose, timeout=timeout)
    return AirQualityReport.from_kml(read_kml(content))


if __name__ == "__main__":
    get_air_quality()
