"""Offline tests for ``get_air_quality`` using a saved piece of AirNow's real file."""

import json

import pytest
from geojson import FeatureCollection

import air_quality_index
from air_quality_index import AirNowError, fetch
from tests.conftest import DATA

LEVELS = {"Good", "Moderate", "UnhealthySG", "Unhealthy", "VeryUnhealthy"}


def test_returns_a_feature_collection(fake_airnow):
    data = air_quality_index.get_air_quality()
    assert isinstance(data, FeatureCollection)
    assert len(data["features"]) == 5
    assert fake_airnow.urls == [
        "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
    ]
    assert fake_airnow.kwargs == {"timeout": 30}


def test_each_feature_is_a_polygon_with_its_level(fake_airnow):
    data = air_quality_index.get_air_quality()
    levels = set()
    for feature in data["features"]:
        assert feature["geometry"]["type"] == "Polygon"
        assert set(feature["properties"]) == {"description", "styleUrl"}
        levels.add(feature["properties"]["styleUrl"].lstrip("#"))
    assert levels == LEVELS


def test_coordinates_are_longitude_latitude_and_zero(fake_airnow):
    data = air_quality_index.get_air_quality()
    ring = data["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    for longitude, latitude, altitude in ring:
        assert -180 <= longitude <= 180
        assert -90 <= latitude <= 90
        assert altitude == 0


def test_a_shape_with_a_hole_has_two_rings(fake_airnow):
    data = air_quality_index.get_air_quality()
    ring_counts = [len(f["geometry"]["coordinates"]) for f in data["features"]]
    assert max(ring_counts) == 2


def test_a_bad_status_fails(fake_airnow):
    fake_airnow.status_code = 503
    with pytest.raises(AirNowError, match="503"):
        air_quality_index.get_air_quality()


def test_matches_what_kml2geojson_5_made_from_the_same_file(fake_airnow):
    """The saved answer was made by the old code, which used kml2geojson 5.1.1."""
    expected = json.loads((DATA / "cur_aqi_pm25_sample.geojson").read_text())
    actual = json.loads(json.dumps(air_quality_index.get_air_quality(repair=False)))
    assert actual == expected


def test_valid_shapes_are_identical_to_the_old_output(fake_airnow):
    """Repair drops the one-point shape and changes nothing else in the sample."""
    expected = json.loads((DATA / "cur_aqi_pm25_sample.geojson").read_text())
    actual = json.loads(json.dumps(air_quality_index.get_air_quality()))
    assert actual["features"] == expected["features"][1:]
    same = json.dumps(actual["features"], sort_keys=True)
    assert same == json.dumps(expected["features"][1:], sort_keys=True)


def test_a_shape_with_only_two_points_is_kept_without_repair(fake_airnow):
    """AirNow really does publish a few shapes that are just one point twice."""
    data = air_quality_index.get_air_quality(repair=False)
    ring = data["features"][0]["geometry"]["coordinates"][0]
    assert len(ring) == 2
    assert ring[0] == ring[1]


KML = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder>{body}</Folder></Document></kml>"""
SQUARE = (
    "<Polygon><outerBoundaryIs><LinearRing><coordinates>"
    "0,0,0 1,0,0 1,1,0 0,0,0</coordinates></LinearRing></outerBoundaryIs></Polygon>"
)


def get_from(monkeypatch, body: str, **options):
    class Reply:
        ok = True
        status_code = 200
        content = KML.format(body=body).encode()

    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: Reply)
    return air_quality_index.get_air_quality(**options)


def test_a_style_without_a_hash_gets_one(monkeypatch):
    body = f"<Placemark><styleUrl>Good</styleUrl>{SQUARE}</Placemark>"
    data = get_from(monkeypatch, body)
    assert data["features"][0]["properties"] == {"styleUrl": "#Good"}


def test_a_shape_with_no_polygon_is_skipped(monkeypatch):
    body = f"<Placemark><styleUrl>#Good</styleUrl></Placemark><Placemark>{SQUARE}</Placemark>"
    data = get_from(monkeypatch, body)
    assert len(data["features"]) == 1


def test_several_polygons_make_a_multipolygon(monkeypatch):
    other = SQUARE.replace("0,0,0 1,0,0 1,1,0 0,0,0", "5,5,0 6,5,0 6,6,0 5,5,0")
    body = f"<Placemark><MultiGeometry>{SQUARE}{other}</MultiGeometry></Placemark>"
    data = get_from(monkeypatch, body)
    assert data["features"][0]["geometry"]["type"] == "MultiPolygon"


def test_a_ring_with_no_coordinates_is_empty_and_extra_tags_are_ignored(monkeypatch):
    body = (
        "<Placemark><Polygon><extrude>1</extrude>"
        "<outerBoundaryIs><LinearRing/></outerBoundaryIs></Polygon></Placemark>"
    )
    data = get_from(monkeypatch, body, repair=False)
    assert data["features"][0]["geometry"]["coordinates"] == [[]]
    assert get_from(monkeypatch, body)["features"] == []
