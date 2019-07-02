import tempfile
import requests
import kml2geojson


def get_air_quality():
    """
    Download air quality index data from AirNow.

    Returns GeoJSON.
    """
    fp = tempfile.NamedTemporaryFile()
    outfile = tempfile.NamedTemporaryFile()
    r = requests.get('https://gist.githubusercontent.com/caseymm/057595ede2227dd90e2b199d9c8682a2/raw/f5d105049d973098b7b529d94f569bc81575a9d8/aqi_data.kml')
    fp.write(r.content)
    print(fp.name)
    kml2geojson.main.convert(str(fp.name), 'test.geojson', separate_folders=False, style_type=None, style_filename='style.json')
