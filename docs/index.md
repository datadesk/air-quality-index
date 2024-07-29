# air-quality-index

Download PM2.5 air quality index data from AirNow

```{contents} Table of contents
:local:
:depth: 2
```

## Installation

```sh
pipenv install air-quality-index
```

## Command-line usage

```sh
Usage: airqualityindex [OPTIONS] COMMAND [ARGS]...

  A command-line interface for downloading PM2.5 air quality index data from AirNow.

Options:
  --help  Show this message and exit.

Commands:
  air-quality  Download latest air quality GeoJSON data
```

Download a GeoJSON of PM2.5 air quality index from AirNow.

```sh
airqualityindex air-quality
```

## Python usage

Import the library.

```python
import air_quality_index
```

Download a GeoJSON of air quality index from AirNow. Returns GeoJSON.

```python
data = air_quality_index.get_air_quality()
```

## Contributing

Install dependencies for development.

```sh
pipenv install --dev
```

Run tests.

```sh
pipenv run python test.py
```

## Developing the CLI

The command-line interface is implemented using Click and setuptools. To install it locally for development inside your virtual environment, run the following installation command, as [prescribed by the Click documentation](https://click.palletsprojects.com/en/7.x/setuptools/#setuptools-integration).

```sh
pipenv run pip install --editable .
```

## Other resources

* Docs: [palewi.re/docs/air-quality-index/](https://palewi.re/docs/air-quality-index/)
* Issues: [github.com/datadesk/air-quality-index/issues](https://github.com/datadesk/air-quality-index/issues)
* Packaging: [pypi.python.org/pypi/air-quality-index](https://pypi.python.org/pypi/air-quality-index)
* Testing: [github.com/datadesk/air-quality-index/actions](https://github.com/datadesk/air-quality-index/actions)
