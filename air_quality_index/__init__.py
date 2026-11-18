"""Download air quality index data from AirNow."""

from __future__ import annotations

import requests
from geojson import Feature, FeatureCollection, MultiPolygon, Polygon

from .kml import read_kml
from .records import AirQualityArea, AirQualityLevel, AirQualityReport

__all__ = [
    "AirQualityArea",
    "AirQualityLevel",
    "AirQualityReport",
    "get_air_quality",
    "get_air_quality_report",
]

URL = "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
"""Where AirNow publishes its current PM2.5 map. It is replaced every hour."""


def get_air_quality() -> FeatureCollection:
    """
    Download PM2.5 air quality index data from AirNow.

    Returns:
        A GeoJSON FeatureCollection. Each feature is a Polygon, with the
        coordinates written as [longitude, latitude, 0], whose properties are
        ``description`` (the HTML AirNow shows in its pop-up) and ``styleUrl``
        (the air quality level, such as "#Good" or "#Unhealthy").

    Raises:
        AssertionError: If AirNow does not answer with a success status.

    Examples:
        >>> data = get_air_quality()
        >>> data["features"][0]["properties"]["styleUrl"]
        '#Good'
    """
    # Get it
    r = requests.get(URL, timeout=30)
    assert r.ok, f"Failed to download data. Status code: {r.status_code}"

    # Read the KML. It is plain XML, so the standard library can do it.
    kml = read_kml(r.content)

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


def get_air_quality_report() -> AirQualityReport:
    """
    Download PM2.5 air quality index data from AirNow as typed records.

    It reads the same file as ``get_air_quality``.

    Returns:
        An ``AirQualityReport`` with the hour the map is for, in UTC, and one
        ``AirQualityArea`` for each patch of the map.

    Raises:
        AssertionError: If AirNow does not answer with a success status.
        ValueError: If the file has no date and hour, or a level this package
            does not know.

    Examples:
        >>> report = get_air_quality_report()
        >>> report.observed_at.tzinfo is not None
        True
        >>> report.areas[0].level.label
        'Good'
    """
    r = requests.get(URL, timeout=30)
    assert r.ok, f"Failed to download data. Status code: {r.status_code}"
    return AirQualityReport.from_kml(read_kml(r.content))


if __name__ == "__main__":
    get_air_quality()
