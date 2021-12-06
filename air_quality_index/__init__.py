import os
import random
import tempfile
import requests
import datetime
import kml2geojson
from datetime import timedelta


API_KEYS = os.environ.get('AIRNOW_KEYS').split(',')


def get_air_quality():
    """
    Download air quality index data from AirNow.

    Returns GeoJSON.
    """
    # Get the current date in the format we need
    formatted_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H")

    # AirNow is usually at least an hour behind UTC time, so go ahead and subract an
    # hour and don't waste a request on it
    formatted_date = _subtract_hour(formatted_date)

    # Make the request
    return _request(formatted_date)


def _request(formatted_date, retry=0):
    # Create temporary file to write request data to
    fp = tempfile.NamedTemporaryFile()

    # Grab a random key
    key = random.choice(API_KEYS)

    # Set the URL
    url = f'http://www.airnowapi.org/aq/kml/PM25/?DATE={formatted_date}&BBOX=-172.322998,15.397743,-59.119873,73.056941&SRS=EPSG:4326&API_KEY={key}'

    # Get it
    r = requests.get(url)

    # Write the content of the request to the temporary file
    fp.write(r.content)

    # Check to see how long the message is. If the message is short, it's telling us that
    # the updated data for that hour doesn't exist yet. If this is the case, subtract
    # an hour and try again.
    if(len(r.content) < 200):
        if retry < 10:
            retry += 1
            formatted_date = _subtract_hour(formatted_date)
            _request(formatted_date, retry=retry)
        else:
            raise ValueError("Request failed")
    else:
        # If the response is good, return it
        return kml2geojson.main.convert(
            str(fp.name),
            separate_folders=False,
            style_type=None,
        )


def _subtract_hour(formatted_date):
    """
    Subtracts an hour from the formatted date and returns a new date with one hour
    less in the correct format.
    """
    hour = int(formatted_date.split('T')[1]) - 1
    if hour < 0:
        return (datetime.datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT23")
    else:
        hour = str(hour)
        if len(hour) < 2:
            hour = f'0{hour}'
        return f'{formatted_date.split("T")[0]}T{hour}'


if __name__ == '__main__':
    get_air_quality()
