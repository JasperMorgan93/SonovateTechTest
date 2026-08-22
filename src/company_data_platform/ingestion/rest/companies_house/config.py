"""Companies House-specific REST configuration."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from company_data_platform.core.config import RestSourceConfig


class CompaniesHouseConfig(RestSourceConfig, BaseSettings):
    """Configuration for calling the Companies House REST API.

    Extends the source-agnostic `RestSourceConfig` with what's specific to
    this source: endpoint paths as fields (not string literals inline in
    the client) and the API key. Loads from environment variables
    prefixed `COMPANIES_HOUSE_` (nested fields via a `__` delimiter, e.g.
    `COMPANIES_HOUSE_RATE_LIMIT__MAX_REQUESTS`).
    """

    model_config = SettingsConfigDict(env_prefix="COMPANIES_HOUSE_", env_nested_delimiter="__")

    base_url: str = "https://api.company-information.service.gov.uk"
    search_companies_path: str = "/search/companies"
    company_profile_path: str = "/company/{company_number}"
    api_key: SecretStr
