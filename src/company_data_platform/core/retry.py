"""Shared retry policy for REST ingestion, built from RetryConfig."""

import requests
import tenacity

from company_data_platform.core.config import RetryConfig


class RetryableStatusError(Exception):
    """Raised internally when a response's status code is retryable.

    This is caught and retried only by the `tenacity.Retrying` built by
    `build_retrying` — it never escapes to application code.
    """

    def __init__(self, response: requests.Response) -> None:
        super().__init__(f"Retryable status {response.status_code} from {response.url}")
        self.response = response


def build_retrying(config: RetryConfig) -> tenacity.Retrying:
    """Build a `tenacity.Retrying` from `RetryConfig`.

    Retries `RetryableStatusError` and transient network errors
    (connection failures, timeouts) with exponential backoff and
    optional jitter; reraises the last exception once attempts are
    exhausted rather than raising tenacity's own `RetryError`.
    """
    wait = (
        tenacity.wait_exponential_jitter(initial=config.backoff_base_seconds, max=config.backoff_max_seconds)
        if config.jitter
        else tenacity.wait_exponential(multiplier=config.backoff_base_seconds, max=config.backoff_max_seconds)
    )
    return tenacity.Retrying(
        stop=tenacity.stop_after_attempt(config.max_attempts),
        wait=wait,
        retry=tenacity.retry_if_exception_type(
            (RetryableStatusError, requests.ConnectionError, requests.Timeout)
        ),
        reraise=True,
    )
