# tests/unit/ingestion/rest/companies_house/test_client.py
import pytest
import responses

from company_data_platform.core.config import RateLimitConfig, RetryConfig
from company_data_platform.ingestion.rest.companies_house.client import CompaniesHouseClient
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.ingestion.rest.companies_house.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

BASE_URL = "https://example.test/companies-house"


def _config(**overrides) -> CompaniesHouseConfig:
    defaults = dict(
        base_url=BASE_URL,
        api_key="test-api-key",
        rate_limit=RateLimitConfig(max_requests=1000, period_seconds=1.0),
        retry=RetryConfig(max_attempts=3, backoff_base_seconds=0.0, backoff_max_seconds=0.0, jitter=False),
    )
    defaults.update(overrides)
    return CompaniesHouseConfig(**defaults)


@responses.activate
def test_search_companies_parses_response():
    responses.add(
        responses.GET,
        f"{BASE_URL}/search/companies",
        json={
            "items": [{"company_number": "12345678", "title": "SONOVATE LIMITED"}],
            "items_per_page": 20,
            "start_index": 0,
            "total_results": 1,
        },
        status=200,
    )
    client = CompaniesHouseClient(_config())

    result = client.search_companies("sono")

    assert result.total_results == 1
    assert result.items[0].company_number == "12345678"


@responses.activate
def test_get_company_parses_response():
    responses.add(
        responses.GET,
        f"{BASE_URL}/company/12345678",
        json={"company_number": "12345678", "company_status": "active", "type": "ltd"},
        status=200,
    )
    client = CompaniesHouseClient(_config())

    profile = client.get_company("12345678")

    assert profile.company_number == "12345678"
    assert profile.company_type == "ltd"


@responses.activate
def test_search_companies_sends_http_basic_auth_with_api_key_as_username():
    responses.add(
        responses.GET,
        f"{BASE_URL}/search/companies",
        json={"items": [], "total_results": 0},
        status=200,
    )
    client = CompaniesHouseClient(_config(api_key="my-secret-key"))

    client.search_companies("sono")

    auth_header = responses.calls[0].request.headers["Authorization"]
    assert auth_header.startswith("Basic ")


@responses.activate
def test_401_raises_authentication_error_without_retry():
    responses.add(responses.GET, f"{BASE_URL}/company/00000001", status=401)
    client = CompaniesHouseClient(_config())

    with pytest.raises(AuthenticationError):
        client.get_company("00000001")

    assert len(responses.calls) == 1


@responses.activate
def test_404_raises_not_found_error_without_retry():
    responses.add(responses.GET, f"{BASE_URL}/company/00000002", status=404)
    client = CompaniesHouseClient(_config())

    with pytest.raises(NotFoundError):
        client.get_company("00000002")

    assert len(responses.calls) == 1


@responses.activate
def test_422_raises_validation_error_without_retry():
    responses.add(responses.GET, f"{BASE_URL}/company/00000003", status=422)
    client = CompaniesHouseClient(_config())

    with pytest.raises(ValidationError):
        client.get_company("00000003")

    assert len(responses.calls) == 1


@responses.activate
def test_transient_500_then_200_succeeds_after_retry():
    responses.add(responses.GET, f"{BASE_URL}/company/00000004", status=500)
    responses.add(
        responses.GET,
        f"{BASE_URL}/company/00000004",
        json={"company_number": "00000004", "company_status": "active"},
        status=200,
    )
    client = CompaniesHouseClient(_config())

    profile = client.get_company("00000004")

    assert profile.company_number == "00000004"
    assert len(responses.calls) == 2


@responses.activate
def test_429_exhausting_retries_raises_rate_limit_error():
    for _ in range(3):
        responses.add(responses.GET, f"{BASE_URL}/company/00000005", status=429)
    client = CompaniesHouseClient(_config())

    with pytest.raises(RateLimitError):
        client.get_company("00000005")

    assert len(responses.calls) == 3


@responses.activate
def test_iter_all_search_results_paginates_across_multiple_pages():
    responses.add(
        responses.GET,
        f"{BASE_URL}/search/companies",
        json={"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 3},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/search/companies",
        json={"items": [{"company_number": "3"}], "total_results": 3},
        status=200,
    )
    client = CompaniesHouseClient(_config(default_items_per_page=2))

    results = list(client.iter_all_search_results("sono"))

    assert [item.company_number for item in results] == ["1", "2", "3"]
