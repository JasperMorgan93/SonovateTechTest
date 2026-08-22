from company_data_platform.core.config import RateLimitConfig
from company_data_platform.core.rate_limiter import TokenBucketRateLimiter


class _FakeClock:
    """A controllable clock: sleep_fn advances `now` instead of blocking."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start
        self.sleep_calls: list[float] = []

    def time_fn(self) -> float:
        return self.now

    def sleep_fn(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.now += seconds


def test_acquire_does_not_sleep_while_tokens_available():
    clock = _FakeClock()
    limiter = TokenBucketRateLimiter(
        RateLimitConfig(max_requests=2, period_seconds=10.0),
        time_fn=clock.time_fn,
        sleep_fn=clock.sleep_fn,
    )

    limiter.acquire()
    limiter.acquire()

    assert clock.sleep_calls == []


def test_acquire_sleeps_once_bucket_is_exhausted():
    clock = _FakeClock()
    limiter = TokenBucketRateLimiter(
        RateLimitConfig(max_requests=1, period_seconds=10.0),
        time_fn=clock.time_fn,
        sleep_fn=clock.sleep_fn,
    )

    limiter.acquire()
    limiter.acquire()

    assert len(clock.sleep_calls) == 1
    assert clock.sleep_calls[0] == 10.0


def test_acquire_refills_after_the_configured_period():
    clock = _FakeClock()
    limiter = TokenBucketRateLimiter(
        RateLimitConfig(max_requests=1, period_seconds=10.0),
        time_fn=clock.time_fn,
        sleep_fn=clock.sleep_fn,
    )

    limiter.acquire()
    clock.now += 10.0
    limiter.acquire()

    assert clock.sleep_calls == []
