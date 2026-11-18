# air-quality-index

Download the current air quality map from [AirNow](https://www.airnow.gov/)

```{contents} Table of contents
:local:
:depth: 2
```

## Read this first

**This is a copy of AirNow's PM2.5 map. It is not an official source of health advice.** Official air quality information and guidance comes from [AirNow](https://www.airnow.gov/), which is run by the U.S. Environmental Protection Agency (EPA) with other agencies. Check there, and with your local health agency, before you tell anyone what to do about the air.

What the data is:

* AirNow's current map of PM2.5, the fine particles in smoke and haze. It comes from the file `cur_aqi_pm25.kml` on AirNow's file server.
* A set of colored patches. Each patch has one air quality level, from "Good" to "Hazardous".
* Replaced by AirNow every hour. The hour it is for is in the file, and in `observed_at` on the typed report. When we checked on 18 November 2026, the file for the 14:00 UTC hour had been written at 15:31 UTC.

What the data is not:

* It does not give exact index numbers. It gives the level only.
* It does not cover ozone or other pollutants.
* It is not a reading at your street. The patches are drawn from monitors, so they smooth over a lot of ground.
* It is not fully checked. On its "about the data" page AirNow says the data in AirNow "are not subjected to the full validation used to officially submit and certify data" for the EPA's regulatory records, and is used to report the AQI to the public.
* It is not a history. The package only reads the latest file.

```{note}
We could not find a terms-of-use page or credit line for AirNow's data files, so none is quoted here. Credit AirNow and the monitoring agencies that supply its data, and check AirNow's own site for current terms before you republish the map.
```

## Installation

```bash
uv add air-quality-index
```

## Quick start

From the shell, print the current map as GeoJSON.

```bash
airqualityindex air-quality > air-quality.geojson
```

From Python, ask for typed records.

```python
import air_quality_index

report = air_quality_index.get_air_quality_report()
print(report.observed_at)
for area in report.areas:
    print(area.level.label, area.level.aqi_range)
```

## The levels

These are the six levels of the Air Quality Index (AQI), as AirNow lists them on its [AQI basics page](https://www.airnow.gov/aqi/aqi-basics/).

| Level | AirNow's name | Index numbers | Python value |
| --- | --- | --- | --- |
| Green | Good | 0 to 50 | `AirQualityLevel.GOOD` |
| Yellow | Moderate | 51 to 100 | `AirQualityLevel.MODERATE` |
| Orange | Unhealthy for Sensitive Groups | 101 to 150 | `AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS` |
| Red | Unhealthy | 151 to 200 | `AirQualityLevel.UNHEALTHY` |
| Purple | Very Unhealthy | 201 to 300 | `AirQualityLevel.VERY_UNHEALTHY` |
| Maroon | Hazardous | 301 and higher | `AirQualityLevel.HAZARDOUS` |

In short: at Good, AirNow says the air is satisfactory and pollution poses little or no risk. At Moderate, unusually sensitive people may be at risk. At Unhealthy for Sensitive Groups, sensitive people may feel health effects. At Unhealthy, some of the general public may feel effects. Very Unhealthy is a health alert, and Hazardous is a health warning of emergency conditions. Read AirNow's page for its full wording.

`AirQualityLevel.UNAVAILABLE` is also in the code, because AirNow's file defines a style for it. We have not seen it in the data. In `aqi_range`, Hazardous ends at 500, the top of the scale, and Unavailable has no range (`None`).

## Field reference

### GeoJSON from `get_air_quality`

A `FeatureCollection`. Each feature is one patch.

| Field | What it is |
| --- | --- |
| `geometry` | A `Polygon`, or a `MultiPolygon` where a repair split a shape in two. The first ring is the outer edge, any other rings are holes. Points are `[longitude, latitude, 0]`, rounded to six decimal places. With `repair=False`, the shapes are exactly as AirNow wrote them, including the few that are invalid or are one point written twice. |
| `properties.styleUrl` | The level, as AirNow names it: `#Good`, `#Moderate`, `#UnhealthySG`, `#Unhealthy`, `#VeryUnhealthy` or `#Hazardous`. |
| `properties.description` | The HTML that AirNow shows when you click the patch. It holds the level's name and a link to AirNow. |

### Typed records from `get_air_quality_report`

`AirQualityReport`:

| Field | What it is |
| --- | --- |
| `observed_at` | The hour the map is for, as a time zone aware `datetime` in UTC. Read from the folder name in the file, such as `1hr_pm25_usa_202611181400_`. The file does not say the zone. UTC fits when it was published, because the file was written after that hour. |
| `areas` | A tuple of `AirQualityArea`. |

`AirQualityArea`:

| Field | What it is |
| --- | --- |
| `level` | An `AirQualityLevel`. It has `label` (plain name) and `aqi_range` (lowest and highest index number). |
| `label` | The level's name as AirNow wrote it in the pop-up. |
| `polygon` | A tuple of rings. Each ring is a tuple of `(longitude, latitude)` pairs, unrounded. If the shape has several polygons, all their rings are listed one after another. |
| `polygons` | The same outline kept as separate polygons, each a tuple of rings. Use this when a repair has made a shape into several. |
| `description` | The pop-up HTML. |

## Command-line usage

```bash
Usage: airqualityindex [OPTIONS] COMMAND [ARGS]...

  A command-line interface for downloading PM2.5 air quality index data from
  AirNow.

Options:
  --help  Show this message and exit.

Commands:
  air-quality  Download latest air quality GeoJSON data
```

```bash
airqualityindex air-quality --timeout 60 --verbose
```

| Option | What it does |
| --- | --- |
| `--timeout` | Seconds to wait for AirNow on each try. The default is 30. |
| `--verbose` | Print each request to standard error, so the GeoJSON on standard output stays clean. |
| `--repair/--no-repair` | Repair invalid shapes (the default), or keep them exactly as AirNow wrote them. |

If AirNow cannot be reached, the command prints one line starting with `Error:` and exits with code 1.

## Python usage

```python
import air_quality_index

data = air_quality_index.get_air_quality()
report = air_quality_index.get_air_quality_report(timeout=60)
```

Both take `verbose`, `timeout`, `get` and `repair`.

### Reliable downloads

A request waits up to `timeout` seconds, 30 by default. It is tried up to four times when AirNow cannot be reached, takes too long, or answers with a server error or "too many requests". The wait doubles each time, starting at about 2 seconds. Anything else, such as "not found", fails at once.

Two errors can be raised:

* `AirNowError`, when AirNow cannot be reached or answers with an error. It has `url` and `status_code`.
* `AirNowDataError`, when the file arrives but cannot be read. It is also a `ValueError`.

### Use your own request function

Pass `get` to send the request through your own helper. It is called as `get(url, timeout=seconds)` and must return something with `status_code` and `content`. The `Fetcher` and `Reply` types describe it.

```python
import requests

import air_quality_index
from air_quality_index import Reply


def my_get(url: str, *, timeout: float) -> Reply:
    return requests.get(url, timeout=timeout, headers={"User-Agent": "my-project"})


data = air_quality_index.get_air_quality(get=my_get)
```

If your function raises one of the `requests` library's errors, the package tries again, as it does for its own requests. Any other error is passed on to you.

### Repairing invalid shapes

A few of the shapes in AirNow's file are not valid polygons: an edge crosses itself like a bow tie, a hole pokes outside its shape, or the shape is a single point written twice. Mapping software can refuse or mis-draw these. In AirNow's file of 18 November 2026 (16:00 UTC, 120 shapes), 5 needed this: 3 had edges that crossed, 1 had a broken hole, and 1 was a single point.

By default the package repairs them with [shapely](https://shapely.readthedocs.io/). A shape that is already valid is not touched: same points, same order, same rounding as before. A repaired shape may come back as a `MultiPolygon`, because mending a bow tie makes two shapes. Only areas are kept: stray lines and points are thrown away, and a shape with no area left is left out.

Pass `repair=False` to `get_air_quality` or `get_air_quality_report` (or `--no-repair` on the command) to get every shape exactly as AirNow wrote it, as version 2.1.0 did.

```python
data = air_quality_index.get_air_quality()  # valid shapes
raw = air_quality_index.get_air_quality(repair=False)  # as AirNow wrote them
```

The repair is also available on its own: `repair_polygons(placemark.polygons)` returns a GeoJSON `Polygon` or `MultiPolygon` (or `None`), and `repair_polygon_list` returns the same polygons as lists.

**This adds shapely, and with it numpy, as dependencies.** On Linux with Python 3.13 they take about 64 MB on disk (numpy about 56 MB, shapely about 8 MB) and about 18 MB to download. Both install from ready-made wheels on Python 3.11 to 3.14.

### Lower-level functions

`get_air_quality` downloads AirNow's file and turns it into GeoJSON in one step. If you need the shapes as AirNow wrote them, or the hour the map is for, use the two steps it is made from:

* `download_kml()` returns the bytes of AirNow's file. It takes `verbose`, `timeout`, `tries` and `get`, and retries and raises `AirNowError` just like the other functions.
* `read_kml(content)` turns those bytes into a `KMLFile`. It has `name`, the folder name AirNow gave the file (for example `1hr_pm25_usa_202611181400_`, which holds the hour in UTC), and `placemarks`, the shapes in file order. Each `Placemark` has `properties` (`styleUrl` and `description`) and `polygons`. Each polygon is a list of rings, the outer ring first and then any holes, and each point is `[longitude, latitude, altitude]`, unrounded. Shapes with no polygon are kept, with an empty list.

```python
import air_quality_index
from air_quality_index import AirQualityReport, download_kml, read_kml

kml = read_kml(download_kml())
report = AirQualityReport.from_kml(kml)
print(report.observed_at)  # the hour as a UTC datetime
for shape in kml.placemarks:
    print(shape.properties["styleUrl"], len(shape.polygons))
```

`DEFAULT_TIMEOUT` and `DEFAULT_TRIES` are the default seconds and number of tries. `KMLFile` and `Placemark` are exported so you can name them in type hints.

## Contributing

This repository's history is about 558 MB, because scraped data files were saved to it. Clone only the latest version:

```bash
git clone --depth 1 https://github.com/datadesk/air-quality-index.git
```

Install what you need, then run the checks.

```bash
make install
make check
```

`make check` runs the tests with coverage and fails if the tests run less than 95% of the package's code, counting every if/else path. `make test-fast` runs them without coverage. In the automated checks, the newest Python version runs with coverage.

`make test-live` runs the tests that call AirNow's real site. The other tests use a small piece of AirNow's real file saved in `tests/data`, so they work offline.

## Other resources

* Docs: [palewi.re/docs/air-quality-index/](https://palewi.re/docs/air-quality-index/)
* Issues: [github.com/datadesk/air-quality-index/issues](https://github.com/datadesk/air-quality-index/issues)
* Packaging: [pypi.python.org/pypi/air-quality-index](https://pypi.python.org/pypi/air-quality-index)
* Testing: [github.com/datadesk/air-quality-index/actions](https://github.com/datadesk/air-quality-index/actions)
