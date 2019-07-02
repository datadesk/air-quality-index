import os
import tempfile
import requests
import kml2geojson
import datetime
from datetime import timedelta


API_KEY = os.environ.get('API_KEY')


def get_air_quality():
    """
    Download air quality index data from AirNow.

    Returns GeoJSON.
    """
    formatted_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H")
    # Make the request
    return _request(formatted_date)


def _request(formatted_date):
    print(formatted_date)
    # Create temporary file to write request data to
    fp = tempfile.NamedTemporaryFile()
    # Create temporary directory that kml2geojson will write file to
    outdir = tempfile.TemporaryDirectory()
    url = f'http://www.airnowapi.org/aq/kml/PM25/?DATE={formatted_date}&BBOX=-172.322998,15.397743,-59.119873,73.056941&SRS=EPSG:4326&API_KEY={API_KEY}'
    r = requests.get(url)
    # Write the content of the request to the temporary file
    fp.write(r.content)
    # print(r.content)
    try:
        # kml2geojson takes a file name and an output director, so we pass in the temporary
        # file and output directory that we created.
        kml2geojson.main.convert(str(fp.name), outdir.name, separate_folders=False, style_type=None, style_filename='style.json')
        # We don't know the name of the geojson file since it's a tempfile, so open the temporary
        # folder that we created and pull the first file.
        with open(f'{outdir.name}/{os.listdir(outdir.name)[0]}') as f:
            return f.read()
    except Exception:
        # Keep subtracting an hour until we get some data
        hour = int(formatted_date.split('T')[1]) - 1
        if hour < 0:
            formatted_date = (datetime.datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT23")
        else:
            hour = str(hour)
            if len(hour) < 2:
                hour = f'0{hour}'
            formatted_date = f'{formatted_date.split("T")[0]}T{hour}'
        _request(formatted_date)
