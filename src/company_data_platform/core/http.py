"""A thin requests.Session wrapper applying a default timeout."""

from typing import Any

import requests


class HttpClient:
    """Wraps a `requests.Session`, applying the configured timeout to every
    request unless the caller explicitly overrides it."""

    def __init__(self, timeout_seconds: float, session: requests.Session | None = None) -> None:
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Issue an HTTP request, defaulting `timeout` to the configured value."""
        kwargs.setdefault("timeout", self._timeout_seconds)
        return self._session.request(method, url, **kwargs)
