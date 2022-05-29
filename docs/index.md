```{include} _templates/nav.html
```

# air-quality-index

Download air quality index data from AirNow

## Installation

```sh
pipenv install air_quality_index
```

## Command-line usage

```sh
Usage: airqualityindex [OPTIONS] COMMAND [ARGS]...

  A command-line interface for downloading air quality index data from AirNow.

Options:
  --help  Show this message and exit.

Commands:
  air-quality  Download latest air quality GeoJSON data
```

Download a GeoJSON of air quality index from AirNow.

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

In order to use this package, you'll need to obtain an API key from [AirNow](https://docs.airnowapi.org/) and set it as a variable in your environment as `AIRNOW_KEYS`. More than one key can be supplied by comma delimiting the string.

```sh
export AIRNOW_KEYS='YOURKEYS,GOHERE'
```

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
