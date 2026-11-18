# air-quality-index

Download the current air quality map from [AirNow](https://www.airnow.gov/), as GeoJSON or typed Python records.

**This is a copy of AirNow's PM2.5 map. It is not an official source of health advice.** For guidance on what to do about the air where you are, use [AirNow](https://www.airnow.gov/) and your local health agency.

## Install

```sh
uv add air-quality-index
```

## Use it from the command line

```sh
airqualityindex air-quality > air-quality.geojson
airqualityindex air-quality --timeout 60 --verbose
```

## Use it from Python

```python
import air_quality_index

data = air_quality_index.get_air_quality()  # GeoJSON
report = air_quality_index.get_air_quality_report()  # typed records
print(report.observed_at, len(report.areas))
for area in report.areas:
    print(area.level.label, area.level.aqi_range)
```

## Use your own request function

Some projects send every web request through their own helper, for shared retries, logging or proxy settings. Pass that helper as `get` and the package will use it instead of `requests.get`. It is called like `get(url, timeout=seconds)` and must return something with a `status_code` and the file's `content` as bytes. The timeout and the retries still work, and failures still raise `AirNowError`.

```python
import requests

import air_quality_index
from air_quality_index import Reply


def my_get(url: str, *, timeout: float) -> Reply:
    return requests.get(url, timeout=timeout, headers={"User-Agent": "my-project"})


data = air_quality_index.get_air_quality(get=my_get)
```

## Repairing invalid shapes

A few of the shapes in AirNow's file are not valid polygons: an edge crosses itself like a bow tie, a hole pokes outside its shape, or the shape is a single point written twice. Mapping software can refuse or mis-draw these. In AirNow's file of 18 November 2026 (16:00 UTC, 120 shapes), 5 needed this: 3 had edges that crossed, 1 had a broken hole, and 1 was a single point.

By default the package repairs them with [shapely](https://shapely.readthedocs.io/). A shape that is already valid is not touched: same points, same order, same rounding as before. A repaired shape may come back as a `MultiPolygon`, because mending a bow tie makes two shapes. Only areas are kept: stray lines and points are thrown away, and a shape with no area left is left out.

Pass `repair=False` to `get_air_quality` or `get_air_quality_report` (or `--no-repair` on the command) to get every shape exactly as AirNow wrote it, as version 2.1.0 did.

```python
data = air_quality_index.get_air_quality()  # valid shapes
raw = air_quality_index.get_air_quality(repair=False)  # as AirNow wrote them
```

The repair is also available on its own: `repair_polygons(placemark.polygons)` returns a GeoJSON `Polygon` or `MultiPolygon` (or `None`), and `repair_polygon_list` returns the same polygons as lists.

**This adds shapely, and with it numpy, as dependencies.** On Linux with Python 3.13 they take about 64 MB on disk (numpy about 56 MB, shapely about 8 MB) and about 18 MB to download. Both install from ready-made wheels on Python 3.11 to 3.14.

## Lower-level functions

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

## Things to know

* **It shows the level, not a number.** AirNow's file says which air quality level each patch of the map is in, such as "Good" or "Unhealthy". It does not say the exact index number. The documentation lists the number range for each level.
* **It covers PM2.5 only.** PM2.5 is fine particles, such as wildfire smoke. Ozone and other pollutants are not in this file.
* **It is fairly fresh.** AirNow replaces the file every hour, and the hour it is for is in `report.observed_at`. This package does not keep old copies.
* **The data is not fully checked.** AirNow says its data "are not subjected to the full validation used to officially submit and certify data" for the EPA's regulatory records.
* **Shapes are repaired by default.** See above. It changes only the few invalid shapes, and `repair=False` turns it off.
* **Downloads retry.** A request waits 30 seconds, then tries again on network errors and server errors, and raises `air_quality_index.AirNowError` if it still fails.
* **AI helped write this package.** AI tools assisted in writing its code, tests and documentation. A person directed and reviewed the work.

The documentation has the field reference and the notes on AirNow's data.

## Working on the code

This repository's full history is about 558 MB, because the scraped data files were saved to it for years. Copy only the latest version:

```bash
git clone --depth 1 https://github.com/datadesk/air-quality-index.git
```

### Links

* Docs: [palewi.re/docs/air-quality-index/](https://palewi.re/docs/air-quality-index/)
* Issues: [github.com/datadesk/air-quality-index/issues](https://github.com/datadesk/air-quality-index/issues)
* Packaging: [pypi.python.org/pypi/air-quality-index](https://pypi.python.org/pypi/air-quality-index)
* Testing: [github.com/datadesk/air-quality-index/actions](https://github.com/datadesk/air-quality-index/actions)
