"""Offline tests for ``get_air_quality`` using a saved piece of AirNow's real file."""

import pytest
from geojson import FeatureCollection

import air_quality_index

LEVELS = {"Good", "Moderate", "UnhealthySG", "Unhealthy", "VeryUnhealthy"}


def test_returns_a_feature_collection(fake_airnow):
    data = air_quality_index.get_air_quality()
    assert isinstance(data, FeatureCollection)
    assert len(data["features"]) == 6
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
    with pytest.raises(AssertionError, match="503"):
        air_quality_index.get_air_quality()
