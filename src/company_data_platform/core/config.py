"""Shared, source-agnostic configuration shapes for REST ingestion.

These are injected into clients, rate limiters, and retry policies rather
than read from globals, so tests can construct small, fast configs without
touching real settings or sleeping (see docs/architecture.md section 6).
"""

from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    """Token bucket parameters for a REST source's rate limit."""

    max_requests: int = 600
    period_seconds: float = 300.0
    max_concurrency: int = 1


class RetryConfig(BaseModel):
    """Retry policy parameters shared by every REST source.

    `retryable_statuses` lists HTTP status codes worth retrying (rate
    limit responses and transient server errors); every other status is a
    permanent failure raised immediately, never retried.
    """

    max_attempts: int = 5
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    jitter: bool = True
    retryable_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})


class RestSourceConfig(BaseModel):
    """Base configuration shape for any REST-based ingestion source."""

    base_url: str
    timeout_seconds: float = 10.0
    default_items_per_page: int = 100
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
