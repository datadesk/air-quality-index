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

## Things to know

* **It shows the level, not a number.** AirNow's file says which air quality level each patch of the map is in, such as "Good" or "Unhealthy". It does not say the exact index number. The documentation lists the number range for each level.
* **It covers PM2.5 only.** PM2.5 is fine particles, such as wildfire smoke. Ozone and other pollutants are not in this file.
* **It is fairly fresh.** AirNow replaces the file every hour, and the hour it is for is in `report.observed_at`. This package does not keep old copies.
* **The data is not fully checked.** AirNow says its data "are not subjected to the full validation used to officially submit and certify data" for the EPA's regulatory records.
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
