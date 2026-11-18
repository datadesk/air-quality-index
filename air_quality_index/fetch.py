"""Download AirNow's air quality file, with a timeout and retries."""

from __future__ import annotations

import random
import sys
import time
from typing import Protocol

import requests

from .errors import AirNowError

URL = "https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/cur_aqi_pm25.kml"
"""Where AirNow publishes its current PM2.5 map. AirNow replaces the file every hour."""

DEFAULT_TIMEOUT = 30.0
"""How many seconds to wait for AirNow before giving up on one attempt."""

DEFAULT_TRIES = 4
"""How many times to try before raising an error."""

RETRY_STATUS_CODES = frozenset({408, 429})
"""Statuses worth another try. Every 5xx status is also worth another try."""


class Reply(Protocol):
    """What a request function must hand back: a status code and the file's bytes.

    A ``requests.Response`` fits this.
    """

    @property
    def status_code(self) -> int:
        """The web status, such as 200 or 404."""
        ...

    @property
    def content(self) -> bytes:
        """The body of the reply, as bytes."""
        ...


class Fetcher(Protocol):
    """A function that makes a web request for this package.

    Pass one as ``get`` to add retries, logging or custom headers. ``requests.get``
    fits this, and is the default.

    Examples:
        >>> import requests
        >>> fetcher: Fetcher = requests.get
    """

    def __call__(self, url: str, *, timeout: float) -> Reply:
        """Request a web address.

        Args:
            url: The address to request.
            timeout: The seconds to wait before giving up.

        Returns:
            The reply.
        """
        ...


def download_kml(
    verbose: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    tries: int = DEFAULT_TRIES,
    get: Fetcher | None = None,
) -> bytes:
    """Download the bytes of AirNow's current PM2.5 map file, as AirNow wrote them.

    Use this with ``read_kml`` when you want the shapes as they are in the file,
    or the hour the file is for. ``get_air_quality`` does both steps and gives
    you GeoJSON.

    A download is tried again when AirNow cannot be reached, takes too long, or
    answers with a server error or "too many requests". The wait before each new
    try doubles, starting at 2 seconds. Any other bad status, such as "not
    found", fails right away.

    Args:
        verbose: Print each request to standard error. Defaults to False.
        timeout: Seconds to wait for AirNow on each try. Defaults to 30.
        tries: How many tries to make in all. Defaults to 4.
        get: A function that makes the web request, such as ``requests.get``
            (the default). It is called as ``get(url, timeout=seconds)`` and
            must return something with ``status_code`` and ``content``. Its
            ``requests`` errors are retried like the default's. Any other error
            it raises is passed on untouched.

    Returns:
        The bytes of the file.

    Raises:
        AirNowError: If every try fails, or AirNow answers with a status that
            is not worth trying again.

    Examples:
        >>> class Reply:
        ...     status_code = 200
        ...     content = b"<kml></kml>"
        >>> download_kml(get=lambda url, *, timeout: Reply())
        b'<kml></kml>'
        >>> content = download_kml()  # asks AirNow
        >>> content = download_kml(timeout=60, tries=2, verbose=True)
    """
    fetch: Fetcher = get or requests.get
    problem = None
    for attempt in range(max(tries, 1)):
        if attempt:
            time.sleep(2**attempt + random.random())
        if verbose:
            print(f"Requesting {URL}", file=sys.stderr)
        try:
            response = fetch(URL, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            problem = AirNowError(f"Could not reach AirNow at {URL}: {error}", url=URL)
            continue
        except requests.RequestException as error:
            raise AirNowError(f"Request to {URL} failed: {error}", url=URL) from error

        status = response.status_code
        if status >= 500 or status in RETRY_STATUS_CODES:
            problem = AirNowError(
                f"AirNow sent back status {status} for {URL}",
                url=URL,
                status_code=status,
            )
            continue
        if status >= 400:
            raise AirNowError(
                f"AirNow sent back status {status} for {URL}",
                url=URL,
                status_code=status,
            )
        return response.content

    assert problem is not None
    raise problem
