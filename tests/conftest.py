"""Shared test setup that keeps the tests off AirNow's real website."""

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


class FakeResponse:
    """A stand-in for a ``requests`` response."""

    def __init__(self, content: bytes = b"", status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code
        self.ok = status_code < 400


@pytest.fixture
def sample_kml() -> bytes:
    """The saved sample of AirNow's file, as bytes.

    It is the real file from AirNow, cut down to six of its 126 shapes so it is
    small: one for each air quality level it had that day, and one shape with a
    hole in it.
    """
    return (DATA / "cur_aqi_pm25_sample.kml").read_bytes()


@pytest.fixture
def fake_airnow(monkeypatch, sample_kml):
    """Replace ``requests.get`` and record the addresses that were asked for."""
    import air_quality_index

    class Fake:
        status_code = 200
        urls: list[str]

    fake = Fake()
    fake.urls = []

    def get(url, *args, **kwargs):
        fake.urls.append(url)
        fake.kwargs = kwargs
        return FakeResponse(sample_kml, fake.status_code)

    monkeypatch.setattr(air_quality_index.requests, "get", get)
    return fake
