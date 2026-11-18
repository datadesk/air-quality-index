"""The lower-level functions are part of the public package."""

import air_quality_index
from air_quality_index import (
    DEFAULT_TIMEOUT,
    DEFAULT_TRIES,
    AirQualityReport,
    KMLFile,
    Placemark,
    download_kml,
    fetch,
    kml,
    read_kml,
)
from tests.conftest import FakeResponse

NEW_NAMES = {
    "DEFAULT_TIMEOUT",
    "DEFAULT_TRIES",
    "KMLFile",
    "Placemark",
    "download_kml",
    "read_kml",
}


def test_the_new_names_are_in_all():
    assert NEW_NAMES <= set(air_quality_index.__all__)
    assert air_quality_index.__all__ == sorted(air_quality_index.__all__)


def test_the_old_import_paths_still_work():
    assert download_kml is fetch.download_kml
    assert DEFAULT_TRIES is fetch.DEFAULT_TRIES
    assert DEFAULT_TIMEOUT is fetch.DEFAULT_TIMEOUT
    assert read_kml is kml.read_kml
    assert KMLFile is kml.KMLFile
    assert Placemark is kml.Placemark


def test_download_then_read_on_the_saved_sample(sample_kml):
    seen = []

    def get(url, *, timeout):
        seen.append((url, timeout))
        return FakeResponse(sample_kml)

    parsed = read_kml(download_kml(get=get, timeout=5))
    assert seen == [(fetch.URL, 5)]
    assert isinstance(parsed, KMLFile)
    assert parsed.name == "1hr_pm25_usa_202611181400_"
    assert len(parsed.placemarks) == 6
    assert all(isinstance(shape, Placemark) for shape in parsed.placemarks)
    # the shape with a hole keeps both of its rings
    assert max(len(shape.polygons[0]) for shape in parsed.placemarks) == 2
    # the hour is available as a time
    report = AirQualityReport.from_kml(parsed)
    assert report.observed_at.isoformat() == "2026-11-18T14:00:00+00:00"
