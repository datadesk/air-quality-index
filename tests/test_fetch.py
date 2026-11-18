"""Tests for the timeout, the retries and the error classes."""

import pytest
import requests

import air_quality_index
from air_quality_index import AirNowDataError, AirNowError, fetch
from tests.conftest import FakeResponse


def script(monkeypatch, answers):
    """Make ``requests.get`` give the answers in order. Exceptions are raised."""
    calls = []

    def get(url, *args, **kwargs):
        calls.append(kwargs)
        answer = answers[min(len(calls), len(answers)) - 1]
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(fetch.requests, "get", get)
    return calls


def test_the_default_timeout_is_passed_on(fake_airnow):
    air_quality_index.get_air_quality()
    assert fake_airnow.kwargs == {"timeout": fetch.DEFAULT_TIMEOUT}


def test_a_custom_timeout_is_passed_on(fake_airnow):
    air_quality_index.get_air_quality(timeout=5)
    assert fake_airnow.kwargs == {"timeout": 5}


def test_a_server_error_is_tried_again(monkeypatch, sample_kml):
    calls = script(monkeypatch, [FakeResponse(b"", 503), FakeResponse(sample_kml)])
    assert fetch.download_kml() == sample_kml
    assert len(calls) == 2


def test_a_network_error_is_tried_again(monkeypatch, sample_kml):
    calls = script(
        monkeypatch,
        [
            requests.ConnectionError("down"),
            requests.Timeout("slow"),
            FakeResponse(sample_kml),
        ],
    )
    assert fetch.download_kml() == sample_kml
    assert len(calls) == 3


def test_too_many_requests_is_tried_again(monkeypatch, sample_kml):
    calls = script(monkeypatch, [FakeResponse(b"", 429), FakeResponse(sample_kml)])
    fetch.download_kml()
    assert len(calls) == 2


def test_giving_up_raises_the_last_problem(monkeypatch):
    calls = script(monkeypatch, [FakeResponse(b"", 502)])
    with pytest.raises(AirNowError, match="502") as caught:
        fetch.download_kml(tries=3)
    assert len(calls) == 3
    assert caught.value.status_code == 502
    assert caught.value.url == fetch.URL


def test_giving_up_after_network_errors_says_so(monkeypatch):
    script(monkeypatch, [requests.ConnectionError("down")])
    with pytest.raises(AirNowError, match="Could not reach AirNow"):
        fetch.download_kml(tries=2)


def test_not_found_fails_right_away(monkeypatch):
    calls = script(monkeypatch, [FakeResponse(b"", 404)])
    with pytest.raises(AirNowError, match="404") as caught:
        fetch.download_kml()
    assert len(calls) == 1
    assert caught.value.status_code == 404


def test_other_request_errors_fail_right_away(monkeypatch):
    calls = script(monkeypatch, [requests.exceptions.InvalidURL("bad")])
    with pytest.raises(AirNowError, match="failed"):
        fetch.download_kml()
    assert len(calls) == 1


def test_at_least_one_try_is_made(monkeypatch, sample_kml):
    calls = script(monkeypatch, [FakeResponse(sample_kml)])
    fetch.download_kml(tries=0)
    assert len(calls) == 1


def test_verbose_prints_to_standard_error(fake_airnow, capsys):
    air_quality_index.get_air_quality(verbose=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert fetch.URL in captured.err


def test_quiet_by_default(fake_airnow, capsys):
    air_quality_index.get_air_quality()
    assert capsys.readouterr().err == ""


def test_the_data_error_is_also_a_value_error():
    assert issubclass(AirNowDataError, ValueError)
    assert issubclass(AirNowDataError, AirNowError)


def test_a_file_that_is_not_xml_is_a_data_error(monkeypatch):
    script(monkeypatch, [FakeResponse(b"<html><body>Oops")])
    with pytest.raises(AirNowDataError, match="could not be read"):
        air_quality_index.get_air_quality()


def test_a_bad_coordinate_is_a_data_error(monkeypatch):
    body = (
        b'<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><Polygon>'
        b"<outerBoundaryIs><LinearRing><coordinates>a,b,c</coordinates>"
        b"</LinearRing></outerBoundaryIs></Polygon></Placemark></kml>"
    )
    script(monkeypatch, [FakeResponse(body)])
    with pytest.raises(AirNowDataError):
        air_quality_index.get_air_quality()


def test_the_report_functions_use_the_same_downloads(fake_airnow):
    air_quality_index.get_air_quality_report(timeout=7)
    assert fake_airnow.kwargs == {"timeout": 7}
