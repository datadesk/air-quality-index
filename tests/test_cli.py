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
    assert len(data["features"]) == 5


def test_timeout_and_verbose_options(fake_airnow):
    result = CliRunner().invoke(cmd, ["air-quality", "--timeout", "9", "--verbose"])
    assert result.exit_code == 0
    assert fake_airnow.kwargs == {"timeout": 9.0}
    json.loads(result.stdout)  # the request line went to stderr, not into the JSON


def test_a_download_error_prints_one_line(fake_airnow):
    fake_airnow.status_code = 404
    result = CliRunner().invoke(cmd, ["air-quality"])
    assert result.exit_code == 1
    assert result.output.startswith("Error: AirNow sent back status 404")
    assert "Traceback" not in result.output


def test_a_tiny_timeout_is_refused():
    result = CliRunner().invoke(cmd, ["air-quality", "--timeout", "0"])
    assert result.exit_code == 2
