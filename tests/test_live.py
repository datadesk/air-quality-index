"""Tests that call AirNow's real website.

They are skipped unless you ask for them with ``make test-live`` (or
``uv run pytest -m live``), because they are slow and fail whenever AirNow is
down.
"""

import pytest

import air_quality_index


@pytest.mark.live
def test_air_quality():
    data = air_quality_index.get_air_quality()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


@pytest.mark.live
def test_air_quality_report():
    report = air_quality_index.get_air_quality_report()
    assert report.observed_at.tzinfo is not None
    assert len(report.areas) > 0
