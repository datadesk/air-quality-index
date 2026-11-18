"""Offline tests of the optional ``get`` argument, with a fake request function."""

import pytest
import requests

import air_quality_index
from air_quality_index import AirNowDataError, AirNowError, fetch
from tests.conftest import FakeResponse


class Recorder:
    """A fake request function that plays back replies and remembers each call."""

    def __init__(self, *replies) -> None:
        self.replies = list(replies)
        self.urls: list[str] = []
        self.timeouts: list[float] = []

    def __call__(self, url: str, *, timeout: float) -> FakeResponse:
        self.urls.append(url)
        self.timeouts.append(timeout)
        reply = self.replies[min(len(self.urls), len(self.replies)) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def good(sample_kml):
    """A good reply."""
    return FakeResponse(sample_kml)


@pytest.fixture
def no_requests(monkeypatch):
    """Fail the test if the package falls back to ``requests.get``."""

    def refuse(*args, **kwargs):
        raise AssertionError("requests.get should not be called")

    monkeypatch.setattr(fetch.requests, "get", refuse)


def test_types_are_exported():
    assert air_quality_index.Fetcher is fetch.Fetcher
    assert air_quality_index.Reply is fetch.Reply
    assert {"Fetcher", "Reply"} <= set(air_quality_index.__all__)


def test_function_is_used_instead_of_requests(no_requests, good):
    get = Recorder(good)
    data = air_quality_index.get_air_quality(get=get)
    assert len(data["features"]) == 6
    assert get.urls == [fetch.URL]


def test_the_report_function_takes_get_too(no_requests, good):
    get = Recorder(good)
    report = air_quality_index.get_air_quality_report(get=get)
    assert len(report.areas) == 6


def test_the_timeout_reaches_the_function(no_requests, good):
    get = Recorder(good)
    air_quality_index.get_air_quality(get=get)
    air_quality_index.get_air_quality(timeout=12, get=get)
    assert get.timeouts == [fetch.DEFAULT_TIMEOUT, 12]


def test_requests_errors_from_the_function_are_retried(no_requests, good):
    get = Recorder(requests.ConnectionError("down"), FakeResponse(b"", 503), good)
    air_quality_index.get_air_quality(get=get)
    assert len(get.urls) == 3


def test_it_gives_up_with_airnow_error(no_requests):
    get = Recorder(FakeResponse(b"", 500))
    with pytest.raises(AirNowError):
        air_quality_index.get_air_quality(get=get)
    assert len(get.urls) == fetch.DEFAULT_TRIES


def test_not_found_is_not_retried(no_requests):
    get = Recorder(FakeResponse(b"", 404))
    with pytest.raises(AirNowError):
        air_quality_index.get_air_quality(get=get)
    assert len(get.urls) == 1


def test_a_bad_file_is_a_data_error(no_requests):
    get = Recorder(FakeResponse(b"not xml"))
    with pytest.raises(AirNowDataError):
        air_quality_index.get_air_quality(get=get)


def test_other_errors_are_passed_on(no_requests):
    get = Recorder(KeyError("mine"))
    with pytest.raises(KeyError):
        air_quality_index.get_air_quality(get=get)


def test_a_reply_needs_only_a_status_and_content(no_requests, sample_kml):
    class Bare:
        status_code = 200
        content = sample_kml

    data = air_quality_index.get_air_quality(get=lambda url, *, timeout: Bare())
    assert len(data["features"]) == 6


def test_the_default_still_uses_requests(fake_airnow):
    air_quality_index.get_air_quality()
    assert fake_airnow.urls == [fetch.URL]
