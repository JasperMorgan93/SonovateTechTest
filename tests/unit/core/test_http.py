import responses

from company_data_platform.core.http import HttpClient


class _RecordingSession:
    """A stub session that records the kwargs it was called with."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        return "fake-response"


def test_request_applies_default_timeout_when_caller_omits_it():
    session = _RecordingSession()
    client = HttpClient(timeout_seconds=5.0, session=session)

    client.request("GET", "https://example.test/thing")

    assert session.calls[0]["timeout"] == 5.0


def test_request_lets_caller_override_timeout():
    session = _RecordingSession()
    client = HttpClient(timeout_seconds=5.0, session=session)

    client.request("GET", "https://example.test/thing", timeout=1.0)

    assert session.calls[0]["timeout"] == 1.0


@responses.activate
def test_request_performs_a_real_http_call_end_to_end():
    responses.add(responses.GET, "https://example.test/thing", json={"ok": True}, status=200)
    client = HttpClient(timeout_seconds=5.0)

    response = client.request("GET", "https://example.test/thing")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
