from company_data_platform.core.config import RateLimitConfig, RestSourceConfig, RetryConfig


def test_rate_limit_config_defaults_match_companies_house_documented_limit():
    config = RateLimitConfig()

    assert config.max_requests == 600
    assert config.period_seconds == 300.0


def test_retry_config_defaults_exclude_permanent_failure_statuses():
    config = RetryConfig()

    assert 429 in config.retryable_statuses
    assert 500 in config.retryable_statuses
    assert 400 not in config.retryable_statuses
    assert 401 not in config.retryable_statuses
    assert 404 not in config.retryable_statuses


def test_rest_source_config_requires_only_base_url():
    config = RestSourceConfig(base_url="https://example.test")

    assert config.base_url == "https://example.test"
    assert config.timeout_seconds == 10.0
    assert config.default_items_per_page == 100
    assert isinstance(config.rate_limit, RateLimitConfig)
    assert isinstance(config.retry, RetryConfig)


def test_rest_source_config_accepts_overridden_nested_configs():
    config = RestSourceConfig(
        base_url="https://example.test",
        rate_limit=RateLimitConfig(max_requests=5, period_seconds=1.0),
        retry=RetryConfig(max_attempts=1),
    )

    assert config.rate_limit.max_requests == 5
    assert config.retry.max_attempts == 1
