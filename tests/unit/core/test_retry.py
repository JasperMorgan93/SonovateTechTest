import pytest

from company_data_platform.core.config import RetryConfig
from company_data_platform.core.retry import RetryableStatusError, build_retrying


class _FakeResponse:
    def __init__(self, status_code: int, url: str = "https://example.test/thing") -> None:
        self.status_code = status_code
        self.url = url


def _fast_retry_config(max_attempts: int) -> RetryConfig:
    return RetryConfig(
        max_attempts=max_attempts, backoff_base_seconds=0.0, backoff_max_seconds=0.0, jitter=False
    )


def test_build_retrying_retries_retryable_status_error_until_success():
    retrying = build_retrying(_fast_retry_config(max_attempts=3))
    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RetryableStatusError(_FakeResponse(500))
        return "ok"

    result = retrying(flaky)

    assert result == "ok"
    assert attempts["count"] == 3


def test_build_retrying_reraises_after_exhausting_attempts():
    retrying = build_retrying(_fast_retry_config(max_attempts=2))
    attempts = {"count": 0}

    def always_fails() -> str:
        attempts["count"] += 1
        raise RetryableStatusError(_FakeResponse(503))

    with pytest.raises(RetryableStatusError):
        retrying(always_fails)

    assert attempts["count"] == 2


def test_build_retrying_does_not_retry_non_retryable_exceptions():
    retrying = build_retrying(_fast_retry_config(max_attempts=5))
    attempts = {"count": 0}

    def raises_value_error() -> str:
        attempts["count"] += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError):
        retrying(raises_value_error)

    assert attempts["count"] == 1
