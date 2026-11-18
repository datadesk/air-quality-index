"""Typed records for the air quality areas AirNow publishes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .errors import AirNowDataError
from .kml import KMLFile, Placemark
from .repair import repair_polygon_list

HOUR_PATTERN = re.compile(r"(\d{12})")
"""Finds the 12 digits (year, month, day, hour, minute) in AirNow's folder name."""

LABEL_PATTERN = re.compile(r"<i>(.*?)</i>", re.DOTALL)
"""Finds the level's name, which AirNow writes in italics inside each pop-up."""


class AirQualityLevel(StrEnum):
    """The air quality levels AirNow draws on its map.

    The value of each is the name AirNow uses in its file, without the "#".
    The ranges are the Air Quality Index (AQI) ranges in the standard table
    published by the U.S. Environmental Protection Agency. AirNow's file does
    not contain the numbers themselves, only the level.

    Examples:
        >>> AirQualityLevel("UnhealthySG").label
        'Unhealthy for Sensitive Groups'
        >>> AirQualityLevel.MODERATE.aqi_range
        (51, 100)
    """

    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_FOR_SENSITIVE_GROUPS = "UnhealthySG"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "VeryUnhealthy"
    HAZARDOUS = "Hazardous"
    UNAVAILABLE = "Unavailable"

    @property
    def label(self) -> str:
        """The name of the level in plain words, such as "Very Unhealthy"."""
        return _LABELS[self]

    @property
    def aqi_range(self) -> tuple[int, int] | None:
        """The lowest and highest AQI number in the level, or None if unavailable."""
        return _RANGES.get(self)


_LABELS = {
    AirQualityLevel.GOOD: "Good",
    AirQualityLevel.MODERATE: "Moderate",
    AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS: "Unhealthy for Sensitive Groups",
    AirQualityLevel.UNHEALTHY: "Unhealthy",
    AirQualityLevel.VERY_UNHEALTHY: "Very Unhealthy",
    AirQualityLevel.HAZARDOUS: "Hazardous",
    AirQualityLevel.UNAVAILABLE: "Unavailable",
}
_RANGES = {
    AirQualityLevel.GOOD: (0, 50),
    AirQualityLevel.MODERATE: (51, 100),
    AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS: (101, 150),
    AirQualityLevel.UNHEALTHY: (151, 200),
    AirQualityLevel.VERY_UNHEALTHY: (201, 300),
    AirQualityLevel.HAZARDOUS: (301, 500),
}


@dataclass(frozen=True, slots=True)
class AirQualityArea:
    """One patch of the AirNow map that has a single air quality level.

    Attributes:
        level: The air quality level.
        label: The level's name as AirNow wrote it in the pop-up, such as
            "Unhealthy for Sensitive Groups".
        polygon: The outline. It is a tuple of rings, the outer ring first and
            then any holes. Each ring is a tuple of (longitude, latitude)
            pairs, in degrees, exactly as AirNow wrote them. If the shape has
            more than one polygon, their rings are listed one after another,
            so use ``polygons`` to tell them apart.
        description: The HTML AirNow shows in its pop-up.
        polygons: The same outline, kept as separate polygons. Each polygon is
            a tuple of rings, like ``polygon``. A shape that was repaired can
            have several.

    Examples:
        >>> placemark = Placemark(
        ...     properties={"styleUrl": "#Good", "description": "<i>Good</i>"},
        ...     polygons=[[[[-100.0, 20.0, 0.0], [-99.0, 20.0, 0.0], [-99.0, 21.0, 0.0], [-100.0, 20.0, 0.0]]]],
        ... )
        >>> area = AirQualityArea.from_placemark(placemark)
        >>> area.level
        <AirQualityLevel.GOOD: 'Good'>
        >>> area.polygon[0][0]
        (-100.0, 20.0)
    """

    level: AirQualityLevel
    label: str
    polygon: tuple[tuple[tuple[float, float], ...], ...]
    description: str
    polygons: tuple[tuple[tuple[tuple[float, float], ...], ...], ...] = ()

    @classmethod
    def from_placemark(
        cls, placemark: Placemark, repair: bool = True
    ) -> AirQualityArea:
        """Make an area from one shape in AirNow's file.

        Args:
            placemark: The shape, as read from the KML.
            repair: Make invalid shapes valid, as ``repair_polygon_list`` does.
                Defaults to True. Pass False to keep the shape exactly as AirNow
                wrote it.

        Returns:
            The area. Its ``polygons`` hold the shape's polygons and its
            ``polygon`` holds all their rings in one tuple. If a repair leaves
            nothing with an area, both are empty.

        Raises:
            AirNowDataError: If the shape has no level, or a level this package does
                not know.

        Examples:
            >>> cls = AirQualityArea
            >>> cls.from_placemark(Placemark({"styleUrl": "#Good"}, [])).label
            'Good'
        """
        style = placemark.properties.get("styleUrl", "").lstrip("#")
        try:
            level = AirQualityLevel(style)
        except ValueError:
            raise AirNowDataError(
                f"AirNow sent an air quality level we do not know: {style!r}"
            ) from None
        description = placemark.properties.get("description", "")
        found = LABEL_PATTERN.search(description)
        label = found.group(1).strip() if found else level.label
        source = (
            repair_polygon_list(placemark.polygons) if repair else placemark.polygons
        )
        polygons = tuple(
            tuple(tuple((point[0], point[1]) for point in ring) for ring in polygon)
            for polygon in source
        )
        rings = tuple(ring for polygon in polygons for ring in polygon)
        return cls(
            level=level,
            label=label,
            polygon=rings,
            description=description,
            polygons=polygons,
        )


@dataclass(frozen=True, slots=True)
class AirQualityReport:
    """AirNow's current PM2.5 map, as typed records.

    Attributes:
        observed_at: The hour the map is for, in UTC. AirNow writes it in the
            name of the folder inside the file.
        areas: The patches of the map. Places AirNow draws as "Good" are
            included.

    Examples:
        >>> from air_quality_index.kml import KMLFile
        >>> kml = KMLFile("1hr_pm25_usa_202611181400_", [])
        >>> AirQualityReport.from_kml(kml).observed_at.isoformat()
        '2026-11-18T14:00:00+00:00'
    """

    observed_at: datetime
    areas: tuple[AirQualityArea, ...]

    @classmethod
    def from_kml(cls, kml: KMLFile, repair: bool = True) -> AirQualityReport:
        """Make a report from what was read out of AirNow's file.

        Args:
            kml: The file's folder name and shapes.
            repair: Make invalid shapes valid. Defaults to True. Shapes with
                no area left are then left out. Pass False to keep every shape
                with a polygon exactly as AirNow wrote it.

        Returns:
            The report. Shapes with no polygon are left out, as they are in the
            GeoJSON.

        Raises:
            AirNowDataError: If the folder name has no date and hour, or a shape has
                a level this package does not know.

        Examples:
            >>> from air_quality_index.kml import KMLFile
            >>> report = AirQualityReport.from_kml(KMLFile("1hr_pm25_usa_202611181400_", []))
            >>> report.areas
            ()
        """
        found = HOUR_PATTERN.search(kml.name or "")
        if not found:
            raise AirNowDataError(
                f"AirNow's file has no date and hour in its folder name: {kml.name!r}"
            )
        observed_at = datetime.strptime(found.group(1), "%Y%m%d%H%M").replace(
            tzinfo=UTC
        )
        areas = tuple(
            area
            for area in (
                AirQualityArea.from_placemark(placemark, repair)
                for placemark in kml.placemarks
                if placemark.polygons
            )
            if area.polygons or not repair
        )
        return cls(observed_at=observed_at, areas=areas)
