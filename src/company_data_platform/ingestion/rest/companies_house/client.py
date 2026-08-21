"""The Companies House REST client: authenticated, rate-limited, retried
calls to /search/companies and /company/{company_number}."""

from collections.abc import Iterator
from typing import Any

import requests

from company_data_platform.core.http import HttpClient
from company_data_platform.core.pagination import paginate_by_start_index
from company_data_platform.core.rate_limiter import TokenBucketRateLimiter
from company_data_platform.core.retry import RetryableStatusError, build_retrying
from company_data_platform.ingestion.rest.companies_house.auth import build_auth
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.ingestion.rest.companies_house.exceptions import (
    AuthenticationError,
    CompaniesHouseError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from company_data_platform.ingestion.rest.companies_house.schemas import (
    CompanyProfile,
    SearchCompaniesResponse,
    SearchResultItem,
)

_VALIDATION_STATUSES = frozenset({400, 406, 422})


class CompaniesHouseClient:
    """Typed calls to the Companies House REST API.

    Applies authentication, rate limiting, and retry uniformly to every
    call via the shared `core/` plumbing; endpoint-specific logic (paths,
    response schemas) lives here.
    """

    def __init__(self, config: CompaniesHouseConfig, session: requests.Session | None = None) -> None:
        self._config = config
        self._http = HttpClient(timeout_seconds=config.timeout_seconds, session=session)
        self._auth = build_auth(config.api_key)
        self._rate_limiter = TokenBucketRateLimiter(config.rate_limit)
        self._retrying = build_retrying(config.retry)

    def search_companies(
        self, query: str, *, items_per_page: int | None = None, start_index: int = 0
    ) -> SearchCompaniesResponse:
        """Call `GET /search/companies`."""
        params = {
            "q": query,
            "items_per_page": items_per_page or self._config.default_items_per_page,
            "start_index": start_index,
        }
        payload = self._request("GET", self._config.search_companies_path, params=params)
        return SearchCompaniesResponse.model_validate(payload)

    def get_company(self, company_number: str) -> CompanyProfile:
        """Call `GET /company/{company_number}`."""
        path = self._config.company_profile_path.format(company_number=company_number)
        payload = self._request("GET", path)
        return CompanyProfile.model_validate(payload)

    def iter_all_search_results(self, query: str) -> Iterator[SearchResultItem]:
        """Paginate `search_companies` to exhaustion."""
        items_per_page = self._config.default_items_per_page

        def fetch_page(start_index: int) -> SearchCompaniesResponse:
            return self.search_companies(query, items_per_page=items_per_page, start_index=start_index)

        yield from paginate_by_start_index(fetch_page, items_per_page)

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._config.base_url}{path}"

        def do_request() -> requests.Response:
            self._rate_limiter.acquire()
            response = self._http.request(method, url, params=params, auth=self._auth)
            if response.status_code in self._config.retry.retryable_statuses:
                raise RetryableStatusError(response)
            return response

        try:
            response = self._retrying(do_request)
        except RetryableStatusError as exc:
            response = exc.response

        return self._parse_or_raise(response)

    def _parse_or_raise(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code == 200:
            return response.json()

        status = response.status_code
        message = f"Companies House API returned {status} for {response.url}"
        if status == 401:
            raise AuthenticationError(status, message)
        if status in _VALIDATION_STATUSES:
            raise ValidationError(status, message)
        if status == 404:
            raise NotFoundError(status, message)
        if status == 429:
            raise RateLimitError(status, message)
        if 500 <= status < 600:
            raise ServerError(status, message)
        raise CompaniesHouseError(status, message)
