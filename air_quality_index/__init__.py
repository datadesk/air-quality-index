"""Download air quality index data from AirNow."""

from __future__ import annotations

import tempfile

import kml2geojson
import requests
from geojson import Feature, FeatureCollection, Polygon


def get_air_quality() -> FeatureCollection:
    """
    Download PM2.5 air quality index data from AirNow.

    Returns GeoJSON FeatureCollection object.
    """
    # Get it
    url = "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
    r = requests.get(url, timeout=30)
    assert r.ok, f"Failed to download data. Status code: {r.status_code}"

    # Create temporary file to write request data to
    fp = tempfile.NamedTemporaryFile()
    fp.write(r.content)

    # Convert the KML to GeoJSON
    geojson_list = kml2geojson.main.convert(
        str(fp.name),
        separate_folders=False,
        style_type=None,
    )

    # Make sure we got one GeoJSON object
    assert len(geojson_list) == 1, f"Expected 1 GeoJSON object, got {len(geojson_list)}"

    # Get the first one
    geojson = geojson_list[0]

    # Tidy it up
    feature_list = []
    for feature in geojson["features"]:
        # Convert to a Polygon and Feature object
        polygon = Polygon(feature["geometry"]["coordinates"])
        feature = Feature(geometry=polygon, properties=feature["properties"])
        # Add to the list
        feature_list.append(feature)

    # Return the results
    return FeatureCollection(feature_list)


if __name__ == "__main__":
    get_air_quality()
