import pytest
from pydantic import ValidationError as PydanticValidationError

from company_data_platform.core.config import RateLimitConfig, RetryConfig
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig


def test_config_has_companies_house_defaults():
    config = CompaniesHouseConfig(api_key="test-key")

    assert config.base_url == "https://api.company-information.service.gov.uk"
    assert config.search_companies_path == "/search/companies"
    assert config.company_profile_path == "/company/{company_number}"
    assert config.api_key.get_secret_value() == "test-key"
    assert isinstance(config.rate_limit, RateLimitConfig)
    assert isinstance(config.retry, RetryConfig)


def test_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("COMPANIES_HOUSE_API_KEY", raising=False)

    with pytest.raises(PydanticValidationError):
        CompaniesHouseConfig()


def test_config_loads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "from-env-key")

    config = CompaniesHouseConfig()

    assert config.api_key.get_secret_value() == "from-env-key"


def test_config_loads_nested_rate_limit_from_environment(monkeypatch):
    monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "test-key")
    monkeypatch.setenv("COMPANIES_HOUSE_RATE_LIMIT__MAX_REQUESTS", "10")

    config = CompaniesHouseConfig()

    assert config.rate_limit.max_requests == 10
