"""Tolerant Pydantic models for Companies House REST response payloads.

Every model here accepts and silently drops unknown fields, and treats
every field Companies House does not structurally guarantee as optional.
This is deliberate: the upstream schema is documented as subject to
change, and ingestion must not break when a new field appears or an
optional one is absent.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    """A postal address as returned by Companies House.

    Used for both a company's registered office and, on other
    resources not modelled yet, a service address — the shape is
    identical either way.
    """

    model_config = ConfigDict(extra="ignore")

    premises: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    locality: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None


class PreviousCompanyName(BaseModel):
    """A prior name a company traded under, per Companies House.

    A company can have zero or many of these; both boundary dates are
    optional because Companies House does not guarantee either is
    populated for every historical entry.
    """

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    effective_from: date | None = None
    ceased_on: date | None = None


class SearchResultItem(BaseModel):
    """A single company result from `GET /search/companies`.

    Only `company_number` is guaranteed present; every other field is
    optional because a search result is a lighter-weight projection
    than a full company profile and Companies House does not document
    a fixed set of fields for it.
    """

    model_config = ConfigDict(extra="ignore")

    company_number: str
    title: str | None = None
    company_type: str | None = None
    company_status: str | None = None
    date_of_creation: date | None = None
    date_of_cessation: date | None = None
    address: Address | None = None
    description: str | None = None
    kind: str | None = None


class SearchCompaniesResponse(BaseModel):
    """The paginated envelope returned by `GET /search/companies`."""

    model_config = ConfigDict(extra="ignore")

    items: list[SearchResultItem] = []
    items_per_page: int | None = None
    start_index: int | None = None
    total_results: int | None = None
    kind: str | None = None


class CompanyProfile(BaseModel):
    """A company profile from `GET /company/{company_number}`.

    This is the root resource per the Companies House guide: treat it
    as authoritative and follow its (not-yet-modelled) resource links
    for deeper data. Only `company_number` and `company_status` are
    guaranteed; every other field — including both list fields, which
    default to empty rather than `None` so callers can iterate without
    a null check — is optional. `company_type` reads from the raw
    `type` key: Companies House names this field differently on the
    profile endpoint than on `/search/companies`.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    company_number: str
    company_status: str
    company_name: str | None = None
    company_status_detail: str | None = None
    company_type: str | None = Field(default=None, alias="type")
    company_subtype: str | None = None
    jurisdiction: str | None = None
    date_of_creation: date | None = None
    date_of_cessation: date | None = None
    registered_office_address: Address | None = None
    sic_codes: list[str] = []
    previous_company_names: list[PreviousCompanyName] = []
