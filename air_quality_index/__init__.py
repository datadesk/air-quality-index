"""Download air quality index data from AirNow."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import requests
from geojson import Feature, FeatureCollection, MultiPolygon, Polygon

URL = "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
"""Where AirNow publishes its current PM2.5 map. It is replaced every hour."""


def _local(tag: str) -> str:
    """Strip the XML namespace from a tag name.

    Args:
        tag: A tag as the XML reader gives it, such as
            "{http://www.opengis.net/kml/2.2}Polygon".

    Returns:
        The plain name, such as "Polygon".

    Examples:
        >>> _local("{http://www.opengis.net/kml/2.2}Polygon")
        'Polygon'
        >>> _local("styleUrl")
        'styleUrl'
    """
    return tag.rsplit("}", 1)[-1]


def _read_ring(node: ET.Element) -> list[list[float]]:
    """Read the coordinates inside a KML ring.

    Args:
        node: A KML ``outerBoundaryIs`` or ``innerBoundaryIs`` element.

    Returns:
        A list of [longitude, latitude, altitude] lists.

    Examples:
        >>> ring = ET.fromstring(
        ...     "<outerBoundaryIs><LinearRing><coordinates>"
        ...     "-102.0,19.9,0 -100.3,19.9,0"
        ...     "</coordinates></LinearRing></outerBoundaryIs>"
        ... )
        >>> _read_ring(ring)
        [[-102.0, 19.9, 0.0], [-100.3, 19.9, 0.0]]
    """
    for child in node.iter():
        if _local(child.tag) == "coordinates":
            return [
                [float(number) for number in point.split(",")]
                for point in (child.text or "").split()
            ]
    return []


def _read_polygon(node: ET.Element) -> list[list[list[float]]]:
    """Read one KML polygon: the outer ring first, then any holes.

    Args:
        node: A KML ``Polygon`` element.

    Returns:
        A list of rings, each a list of [longitude, latitude, altitude] lists.

    Examples:
        >>> polygon = ET.fromstring(
        ...     "<Polygon><outerBoundaryIs><LinearRing><coordinates>"
        ...     "0,0,0 1,0,0 1,1,0 0,0,0</coordinates></LinearRing>"
        ...     "</outerBoundaryIs></Polygon>"
        ... )
        >>> len(_read_polygon(polygon))
        1
    """
    outer = []
    inner = []
    for child in node:
        if _local(child.tag) == "outerBoundaryIs":
            outer.append(_read_ring(child))
        elif _local(child.tag) == "innerBoundaryIs":
            inner.append(_read_ring(child))
    return outer + inner


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
    root = ET.fromstring(r.content)

    # Tidy it up
    feature_list = []
    for placemark in root.iter():
        if _local(placemark.tag) != "Placemark":
            continue

        # The properties AirNow writes for each shape
        properties = {}
        polygons = []
        for node in placemark.iter():
            name = _local(node.tag)
            text = (node.text or "").strip()
            if name == "description" and text:
                properties["description"] = text
            elif name == "styleUrl" and text:
                properties["styleUrl"] = text if text.startswith("#") else "#" + text
            elif name == "Polygon":
                polygons.append(_read_polygon(node))

        # Make a Polygon, or a MultiPolygon if AirNow ever sends several at once
        if not polygons:
            continue
        geometry = (
            Polygon(polygons[0]) if len(polygons) == 1 else MultiPolygon(polygons)
        )
        feature_list.append(Feature(geometry=geometry, properties=properties))

    # Return the results
    return FeatureCollection(feature_list)


if __name__ == "__main__":
    get_air_quality()
