"""Offline tests for the ``airqualityindex`` command."""

import json

from click.testing import CliRunner

from air_quality_index.cli import cmd


def test_help_lists_the_command():
    result = CliRunner().invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "air-quality" in result.output


def test_air_quality_prints_geojson(fake_airnow):
    result = CliRunner().invoke(cmd, ["air-quality"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 6
