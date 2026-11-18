"""Repair the invalid shapes that AirNow sometimes publishes."""

from __future__ import annotations

import shapely
from geojson import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

POLYGON_TYPE = list[list[list[float]]]
"""One polygon as ``read_kml`` returns it: a list of rings, the outer ring first
and then any holes. Each ring is a list of [longitude, latitude, altitude]."""


def _build(polygons: list[POLYGON_TYPE]) -> BaseGeometry | None:
    """Make a shapely shape from polygons, leaving out rings that are too short.

    A ring needs at least four points (the last repeats the first) to enclose
    anything. AirNow publishes a few that are one point written twice. A short
    outer ring drops its whole polygon, and a short hole is dropped by itself.

    Args:
        polygons: The polygons, as ``read_kml`` returns them.

    Returns:
        A ``Polygon`` or ``MultiPolygon``, which may be invalid, or None if no
        polygon has a long enough outer ring.

    Examples:
        >>> _build([[[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]]]).geom_type
        'Polygon'
        >>> _build([[[[1, 2, 0], [1, 2, 0]]]]) is None
        True
    """
    built = []
    for rings in polygons:
        if not rings or len(rings[0]) < 4:
            continue
        holes = [[(p[0], p[1]) for p in ring] for ring in rings[1:] if len(ring) >= 4]
        built.append(shapely.Polygon([(p[0], p[1]) for p in rings[0]], holes))
    if not built:
        return None
    return built[0] if len(built) == 1 else shapely.MultiPolygon(built)


def collect_polygons(geometry: BaseGeometry) -> list[shapely.Polygon]:
    """Pull every polygon out of a shape, however deeply it is nested.

    ``shapely.make_valid`` can answer with a collection that holds a
    ``MultiPolygon`` next to stray lines, and collections can hold other
    collections. This walks all the way down, keeps the polygons, and drops lines
    and points.

    Args:
        geometry: Any shapely shape.

    Returns:
        The non-empty polygons found, in order.

    Examples:
        >>> from shapely import GeometryCollection, LineString, MultiPolygon, Polygon
        >>> square = Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])
        >>> nested = GeometryCollection(
        ...     [GeometryCollection([MultiPolygon([square, square])]), LineString([(0, 0), (1, 1)])]
        ... )
        >>> len(collect_polygons(nested))
        2
    """
    if isinstance(geometry, shapely.Polygon):
        return [] if geometry.is_empty else [geometry]
    # Multi-part shapes and collections both have parts. Lines and points do not.
    return [
        polygon
        for part in getattr(geometry, "geoms", [])
        for polygon in collect_polygons(part)
    ]


def _to_lists(polygon: shapely.Polygon) -> POLYGON_TYPE:
    """Turn a shapely polygon back into rings of [longitude, latitude, 0].

    Args:
        polygon: A shapely polygon.

    Returns:
        The outer ring and then the holes, with altitude 0 on every point, the
        way AirNow writes them.

    Examples:
        >>> _to_lists(shapely.Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]))
        [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0]]]
    """
    rings = [polygon.exterior, *polygon.interiors]
    return [[[float(x), float(y), 0.0] for x, y, *_ in ring.coords] for ring in rings]


def repair_polygon_list(polygons: list[POLYGON_TYPE]) -> list[POLYGON_TYPE]:
    """Make a shape's polygons valid, leaving valid shapes exactly as they are.

    A shape that is already valid comes back as the very same list, untouched.
    An invalid one, such as a polygon whose edge crosses itself or whose hole
    pokes outside it, is repaired with ``shapely.make_valid`` and only the
    areas are kept. Rings of fewer than four points are dropped.

    Args:
        polygons: The polygons of one shape, as in ``Placemark.polygons``.

    Returns:
        The polygons to use. An empty list means nothing with an area was left.

    Examples:
        >>> bowtie = [[[0, 0, 0], [2, 2, 0], [2, 0, 0], [0, 2, 0], [0, 0, 0]]]
        >>> len(repair_polygon_list([bowtie]))
        2
        >>> square = [[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]]
        >>> repair_polygon_list([square]) == [square]
        True
    """
    shape = _build(polygons)
    if shape is None:
        return []
    already_clean = all(len(ring) >= 4 for rings in polygons for ring in rings)
    if already_clean and shape.is_valid:
        return polygons
    return [_to_lists(p) for p in collect_polygons(shapely.make_valid(shape))]


def repair_polygons(polygons: list[POLYGON_TYPE]) -> Polygon | MultiPolygon | None:
    """Make a shape's polygons valid and return them as GeoJSON.

    This is what ``get_air_quality`` uses. Coordinates are rounded to six
    decimal places, as they always have been.

    Args:
        polygons: The polygons of one shape, as in ``Placemark.polygons``.

    Returns:
        A GeoJSON ``Polygon`` if one polygon is left, a ``MultiPolygon`` if
        several are, or None if nothing with an area is left (for example a
        shape that is one point written twice).

    Examples:
        >>> square = [[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]]
        >>> repair_polygons([square])["type"]
        'Polygon'
        >>> bowtie = [[[0, 0, 0], [2, 2, 0], [2, 0, 0], [0, 2, 0], [0, 0, 0]]]
        >>> repair_polygons([bowtie])["type"]
        'MultiPolygon'
        >>> repair_polygons([[[[1, 2, 0], [1, 2, 0]]]]) is None
        True
    """
    fixed = repair_polygon_list(polygons)
    if not fixed:
        return None
    return Polygon(fixed[0]) if len(fixed) == 1 else MultiPolygon(fixed)
