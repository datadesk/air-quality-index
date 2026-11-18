"""Read the KML file that AirNow publishes, using only the standard library."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Placemark:
    """One shape from AirNow's KML file, as it was written.

    Attributes:
        properties: The text AirNow wrote for the shape. It can hold
            ``description`` (the HTML of the pop-up) and ``styleUrl`` (the air
            quality level, such as "#Good"), and leaves out any that are blank.
        polygons: The shape's polygons. Each polygon is a list of rings (the
            outer ring first, then any holes) and each ring is a list of
            [longitude, latitude, altitude] lists.
    """

    properties: dict[str, str] = field(default_factory=dict)
    polygons: list[list[list[list[float]]]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class KMLFile:
    """What was read from AirNow's KML file.

    Attributes:
        name: The name AirNow gave the folder holding the shapes, such as
            "1hr_pm25_usa_202611181400_". It holds the hour of the data. It is
            None if the file has no folder name.
        placemarks: The shapes, in file order.
    """

    name: str | None
    placemarks: list[Placemark]


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


def _read_placemark(node: ET.Element) -> Placemark:
    """Read one ``Placemark`` element.

    Args:
        node: A KML ``Placemark`` element.

    Returns:
        The shape's text properties and polygons. A ``styleUrl`` without a
        leading "#" gets one.

    Examples:
        >>> node = ET.fromstring("<Placemark><styleUrl>Good</styleUrl></Placemark>")
        >>> _read_placemark(node).properties
        {'styleUrl': '#Good'}
    """
    properties = {}
    polygons = []
    for child in node.iter():
        name = _local(child.tag)
        text = (child.text or "").strip()
        if name == "description" and text:
            properties["description"] = text
        elif name == "styleUrl" and text:
            properties["styleUrl"] = text if text.startswith("#") else "#" + text
        elif name == "Polygon":
            polygons.append(_read_polygon(child))
    return Placemark(properties=properties, polygons=polygons)


def read_kml(content: bytes) -> KMLFile:
    """Read the bytes of AirNow's KML file.

    Args:
        content: The bytes of the file.

    Returns:
        The folder name and the shapes.

    Raises:
        xml.etree.ElementTree.ParseError: If the bytes are not XML.

    Examples:
        >>> kml = read_kml(
        ...     b"<kml><Document><Folder><name>1hr_pm25_usa_202611181400_</name>"
        ...     b"<Placemark><styleUrl>#Good</styleUrl></Placemark></Folder></Document></kml>"
        ... )
        >>> kml.name
        '1hr_pm25_usa_202611181400_'
        >>> len(kml.placemarks)
        1
    """
    root = ET.fromstring(content)
    name = None
    placemarks = []
    for node in root.iter():
        tag = _local(node.tag)
        if tag == "Placemark":
            placemarks.append(_read_placemark(node))
        elif tag == "name" and name is None:
            name = (node.text or "").strip() or None
    return KMLFile(name=name, placemarks=placemarks)
