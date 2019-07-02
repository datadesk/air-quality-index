import os
import tempfile
import requests
import kml2geojson


def get_air_quality():
    """
    Download air quality index data from AirNow.

    Returns GeoJSON.
    """
    # Create temporary file to write request data to
    fp = tempfile.NamedTemporaryFile()
    # Create temporary directory that kml2geojson will write file to
    outdir = tempfile.TemporaryDirectory()
    # Make the request
    r = requests.get('https://gist.githubusercontent.com/caseymm/057595ede2227dd90e2b199d9c8682a2/raw/f5d105049d973098b7b529d94f569bc81575a9d8/aqi_data.kml')
    # Write the content of the request to the temporary file
    fp.write(r.content)
    # kml2geojson takes a file name and an output director, so we pass in the temporary
    # file and output directory that we created.
    kml2geojson.main.convert(str(fp.name), outdir.name, separate_folders=False, style_type=None, style_filename='style.json')
    # We don't know the name of the geojson file since it's a tempfile, so open the temporary
    # folder that we created and pull the first file.
    with open(f'{outdir.name}/{os.listdir(outdir.name)[0]}') as f:
        return f.read()
