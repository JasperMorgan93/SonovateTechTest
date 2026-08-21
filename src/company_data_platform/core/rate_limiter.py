"""A token bucket rate limiter shared by every REST ingestion source."""

import threading
import time
from collections.abc import Callable

from company_data_platform.core.config import RateLimitConfig


class TokenBucketRateLimiter:
    """Blocks callers until a request token is available.

    `time_fn`/`sleep_fn` are injected rather than read from the `time`
    module directly, so tests run against a fake clock and never perform
    a real wall-clock wait.
    """

    def __init__(
        self,
        config: RateLimitConfig,
        time_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self._max_requests = config.max_requests
        self._period_seconds = config.period_seconds
        self._time_fn = time_fn
        self._sleep_fn = sleep_fn
        self._lock = threading.Lock()
        self._tokens = float(config.max_requests)
        self._last_refill = time_fn()

    def acquire(self) -> None:
        """Block until a token is available, then consume one."""
        with self._lock:
            self._refill()
            if self._tokens < 1:
                wait_seconds = (1 - self._tokens) * (self._period_seconds / self._max_requests)
                self._sleep_fn(wait_seconds)
                self._refill()
            self._tokens -= 1

    def _refill(self) -> None:
        now = self._time_fn()
        elapsed = now - self._last_refill
        refill_rate = self._max_requests / self._period_seconds
        self._tokens = min(float(self._max_requests), self._tokens + elapsed * refill_rate)
        self._last_refill = now
