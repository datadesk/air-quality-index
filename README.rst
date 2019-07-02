air-quality-index
==============

Download air quality index data from AirNow

Installation
------------

::

    $ pipenv install air_quality_index


Command-line usage
------------------

::

    Usage: airqualityindex [OPTIONS] COMMAND [ARGS]...

      A command-line interface for downloading wildfire data from NASA
      satellites.

      Returns GeoJSON.

    Options:
      --help  Show this message and exit.

    Commands:
      air-quality  Download a GeoJSON of air quality index from AirNow


Download a GeoJSON of air quality index from AirNow. ::

    $ air_quality_index modis


Python usage
------------

Import the library. ::

    >>> import air_quality_index

Download a GeoJSON of air quality index from AirNow. Returns GeoJSON. ::

    >>> data = air_quality_index.get_air_quality()


Contributing
------------

Install dependencies for development. ::

    $ pipenv install --dev

Run tests.::

    $ make test

Shipping new version to PyPI. ::

    $ make ship


Developing the CLI
------------------

The command-line interface is implemented using Click and setuptools. To install it locally for development inside your virtual environment, run the following installation command, as `prescribed by the Click documentation <https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration>`_. ::

    $ pip install --editable .

AirNow API Usage
----------------

In order to use this package, you'll need to obtain an API key from `AirNow <https://docs.airnowapi.org/>`_ and set it as a variable in your environment.
