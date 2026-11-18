"""Tests for repairing AirNow's invalid shapes."""

import json

import pytest
import shapely
from shapely import GeometryCollection, LineString, MultiPolygon, Polygon

import air_quality_index
from air_quality_index import (
    AirQualityReport,
    read_kml,
    repair_polygon_list,
    repair_polygons,
)
from air_quality_index.kml import Placemark
from air_quality_index.repair import collect_polygons
from tests.conftest import DATA, FakeResponse

SQUARE = [[[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 0]]]
BOWTIE = [[[0, 0, 0], [2, 2, 0], [2, 0, 0], [0, 2, 0], [0, 0, 0]]]
BOWTIE_WITH_SPIKE = [
    [[0, 0, 0], [2, 2, 0], [2, 0, 0], [0, 2, 0], [0, 0, 0], [-1, -1, 0], [0, 0, 0]]
]
BAD_HOLE = [
    [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 0]],
    [[3, 3, 0], [6, 3, 0], [6, 6, 0], [3, 6, 0], [3, 3, 0]],
]
ONE_POINT_TWICE = [[[1, 2, 0], [1, 2, 0]]]


def area_of(polygons) -> float:
    return sum(shapely.Polygon(p[0], p[1:]).area for p in polygons)


def test_a_valid_shape_comes_back_unchanged():
    shape = [SQUARE]
    assert repair_polygon_list(shape) is shape


def test_a_valid_shape_gives_the_same_geojson_as_before():
    geometry = repair_polygons([SQUARE])
    assert geometry == {"type": "Polygon", "coordinates": SQUARE_FLOATS}


SQUARE_FLOATS = [[[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 0]]]


def test_a_bowtie_becomes_two_triangles():
    fixed = repair_polygon_list([BOWTIE])
    assert len(fixed) == 2
    assert all(shapely.Polygon(p[0]).is_valid for p in fixed)
    assert area_of(fixed) == pytest.approx(2.0)
    geometry = repair_polygons([BOWTIE])
    assert geometry["type"] == "MultiPolygon"
    assert all(
        point[2] == 0
        for poly in geometry["coordinates"]
        for pt in poly
        for point in [pt[0]]
    )


def test_a_bad_hole_is_repaired():
    shape = shapely.Polygon(BAD_HOLE[0], [BAD_HOLE[1]])
    assert not shape.is_valid
    fixed = repair_polygon_list([BAD_HOLE])
    rebuilt = [shapely.Polygon(p[0], p[1:]) for p in fixed]
    assert all(p.is_valid for p in rebuilt)
    assert area_of(fixed) == pytest.approx(shapely.make_valid(shape).area)
    assert area_of(fixed) > 0


def test_the_copilot_case_keeps_every_repaired_area():
    """make_valid answers with a collection of a MultiPolygon and a line."""
    raw = shapely.Polygon([(x, y) for x, y, _ in BOWTIE_WITH_SPIKE[0]])
    answer = shapely.make_valid(raw)
    kinds = [part.geom_type for part in answer.geoms]
    assert answer.geom_type == "GeometryCollection"
    assert kinds == ["MultiPolygon", "LineString"]

    fixed = repair_polygon_list([BOWTIE_WITH_SPIKE])
    assert len(fixed) == 2
    assert area_of(fixed) == pytest.approx(2.0)
    assert repair_polygons([BOWTIE_WITH_SPIKE])["type"] == "MultiPolygon"


def test_polygons_are_collected_from_collections_inside_collections():
    square = Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])
    other = Polygon([(5, 5), (6, 5), (6, 6), (5, 5)])
    nested = GeometryCollection(
        [
            GeometryCollection(
                [
                    GeometryCollection([MultiPolygon([square, other])]),
                    LineString([(0, 0), (1, 1)]),
                ]
            ),
            shapely.Point(3, 3),
            Polygon(),
        ]
    )
    assert collect_polygons(nested) == [square, other]
    assert collect_polygons(LineString([(0, 0), (1, 1)])) == []


def test_a_shape_that_is_one_point_twice_is_dropped():
    assert repair_polygon_list([ONE_POINT_TWICE]) == []
    assert repair_polygons([ONE_POINT_TWICE]) is None
    assert repair_polygons([]) is None
    assert repair_polygons([[]]) is None


def test_a_short_hole_is_dropped_and_the_polygon_kept():
    fixed = repair_polygon_list([SQUARE + [[[1, 1, 0], [1, 1, 0]]]])
    assert fixed == [SQUARE]


def test_several_valid_polygons_make_a_multipolygon():
    other = [[[10, 10, 0], [11, 10, 0], [11, 11, 0], [10, 10, 0]]]
    geometry = repair_polygons([SQUARE, other])
    assert geometry["type"] == "MultiPolygon"
    assert len(geometry["coordinates"]) == 2


def test_a_shape_with_nothing_but_a_line_is_dropped():
    line = [[[0, 0, 0], [1, 1, 0], [2, 2, 0], [0, 0, 0]]]
    assert repair_polygons([line]) is None


def test_the_real_invalid_shapes(monkeypatch):
    """Four shapes from AirNow's real file: three that need repair, one point."""
    content = (DATA / "invalid_shapes_sample.kml").read_bytes()
    monkeypatch.setattr(
        air_quality_index.fetch.requests,
        "get",
        lambda *a, **k: FakeResponse(content),
    )
    raw = air_quality_index.get_air_quality(repair=False)
    assert len(raw["features"]) == 4
    fixed = air_quality_index.get_air_quality()
    assert len(fixed["features"]) == 3
    for feature in fixed["features"]:
        parts = (
            [feature["geometry"]["coordinates"]]
            if feature["geometry"]["type"] == "Polygon"
            else feature["geometry"]["coordinates"]
        )
        for rings in parts:
            assert shapely.Polygon(rings[0], rings[1:]).is_valid


def test_the_report_repairs_by_default_and_can_skip_it():
    kml = read_kml((DATA / "invalid_shapes_sample.kml").read_bytes())
    repaired = AirQualityReport.from_kml(kml)
    untouched = AirQualityReport.from_kml(kml, repair=False)
    assert len(repaired.areas) == 3
    assert len(untouched.areas) == 4
    assert untouched.areas[0].polygons == (untouched.areas[0].polygon,)
    for area in repaired.areas:
        assert area.polygon == tuple(r for poly in area.polygons for r in poly)


def test_get_air_quality_report_takes_repair(fake_airnow):
    assert len(air_quality_index.get_air_quality_report().areas) == 5
    assert len(air_quality_index.get_air_quality_report(repair=False).areas) == 6


def test_an_area_whose_shape_has_nothing_left_has_empty_outlines():
    placemark = Placemark({"styleUrl": "#Good"}, [ONE_POINT_TWICE])
    area = air_quality_index.AirQualityArea.from_placemark(placemark)
    assert area.polygon == ()
    assert area.polygons == ()
    raw = air_quality_index.AirQualityArea.from_placemark(placemark, repair=False)
    assert raw.polygon == (((1, 2), (1, 2)),)


def test_the_command_has_a_no_repair_option(fake_airnow):
    from click.testing import CliRunner

    from air_quality_index.cli import cmd

    default = json.loads(CliRunner().invoke(cmd, ["air-quality"]).stdout)
    raw = json.loads(CliRunner().invoke(cmd, ["air-quality", "--no-repair"]).stdout)
    assert len(default["features"]) == 5
    assert len(raw["features"]) == 6
