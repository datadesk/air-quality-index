"""Download air quality index data from AirNow."""

from __future__ import annotations

import tempfile

import requests
import kml2geojson


def get_air_quality() -> dict:
    """
    Download PM2.5 air quality index data from AirNow.

    Returns GeoJSON.
    """
    # Get it
    url = "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
    r = requests.get(url, timeout=30)
    assert r.ok, f"Failed to download data. Status code: {r.status_code}"

    # Create temporary file to write request data to
    fp = tempfile.NamedTemporaryFile()
    fp.write(r.content)

    # Convert the KML to GeoJSON
    return kml2geojson.main.convert(
        str(fp.name),
        separate_folders=False,
        style_type=None,
    )


if __name__ == "__main__":
    get_air_quality()
