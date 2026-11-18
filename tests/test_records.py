"""Offline tests for the typed records, using a saved piece of AirNow's real file."""

from datetime import UTC

import pytest

import air_quality_index
from air_quality_index import AirQualityArea, AirQualityLevel, AirQualityReport
from air_quality_index.kml import KMLFile, Placemark, read_kml


def test_the_report_has_its_hour_in_utc(fake_airnow):
    report = air_quality_index.get_air_quality_report()
    assert isinstance(report, AirQualityReport)
    assert report.observed_at.isoformat() == "2026-11-18T14:00:00+00:00"
    assert report.observed_at.tzinfo is UTC


def test_the_areas_match_the_geojson(fake_airnow):
    report = air_quality_index.get_air_quality_report()
    data = air_quality_index.get_air_quality()
    assert len(report.areas) == len(data["features"]) == 5
    for area, feature in zip(report.areas, data["features"], strict=True):
        assert "#" + area.level.value == feature["properties"]["styleUrl"]
        assert len(area.polygon) == len(feature["geometry"]["coordinates"])


def test_labels_come_from_the_popup(fake_airnow):
    report = air_quality_index.get_air_quality_report()
    labels = {area.level: area.label for area in report.areas}
    assert labels[AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS] == (
        "Unhealthy for Sensitive Groups"
    )
    assert labels[AirQualityLevel.VERY_UNHEALTHY] == "Very Unhealthy"
    for level, label in labels.items():
        assert label == level.label


def test_points_are_longitude_then_latitude(fake_airnow):
    report = air_quality_index.get_air_quality_report()
    for area in report.areas:
        for ring in area.polygon:
            for longitude, latitude in ring:
                assert -180 <= longitude <= 0  # the whole sample is in the Americas
                assert 0 <= latitude <= 90


def test_levels_have_ranges_and_names():
    assert AirQualityLevel.GOOD.aqi_range == (0, 50)
    assert AirQualityLevel.HAZARDOUS.aqi_range == (301, 500)
    assert AirQualityLevel.UNAVAILABLE.aqi_range is None
    assert AirQualityLevel("VeryUnhealthy") is AirQualityLevel.VERY_UNHEALTHY


def test_a_missing_label_falls_back_to_the_level_name():
    area = AirQualityArea.from_placemark(
        Placemark({"styleUrl": "#UnhealthySG"}, [[[[0.0, 0.0, 0.0]]]])
    )
    assert area.label == "Unhealthy for Sensitive Groups"
    assert area.description == ""


def test_an_unknown_level_is_an_error():
    with pytest.raises(ValueError, match="Purple"):
        AirQualityArea.from_placemark(Placemark({"styleUrl": "#Purple"}, []))


def test_a_missing_level_is_an_error():
    with pytest.raises(ValueError, match="level"):
        AirQualityArea.from_placemark(Placemark({}, []))


def test_a_folder_name_without_an_hour_is_an_error():
    with pytest.raises(ValueError, match="date and hour"):
        AirQualityReport.from_kml(KMLFile("nothing here", []))
    with pytest.raises(ValueError, match="date and hour"):
        AirQualityReport.from_kml(KMLFile(None, []))


def test_the_whole_sample_file_reads(sample_kml):
    kml = read_kml(sample_kml)
    assert kml.name == "1hr_pm25_usa_202611181400_"
    assert len(kml.placemarks) == 6
