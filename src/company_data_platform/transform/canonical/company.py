"""Canonical models for a company and its related entities.

These are the platform's own model of a company, address, previous name,
SIC code, and search match — not any one source's field names typed 1:1.
A source-specific mapper (e.g. `transform/companies_house/normalizer.py`)
translates that source's raw shape onto these models; a second source
describing companies would target the same models and the same silver
tables. See `docs/data-model.md` for the `silver.*` schema these mirror.

Fields a given source's mapper cannot populate (e.g. `company_subtype`
from a Companies House search result, which doesn't carry it) are simply
left unset rather than removed from the model, so adding a source with
richer data — or a second source altogether — doesn't require a schema
change here.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class _CanonicalModel(BaseModel):
    """Shared config for every canonical model: immutable once constructed.

    Canonical rows are the output of a mapping step, not something callers
    build up incrementally — matches the platform-wide rule that bronze and
    silver rows are never mutated after they're produced.
    """

    model_config = ConfigDict(frozen=True)


class CanonicalCompany(_CanonicalModel):
    """The platform's canonical model of a company.

    Mirrors `silver.company`. `company_number` is the identity — company
    name is never used as a key, per the Companies House guide.
    """

    company_number: str
    title: str
    company_type: str
    source_system: str
    source_retrieved_at: datetime
    company_status: str | None = None
    company_status_detail: str | None = None
    company_subtype: str | None = None
    jurisdiction: str | None = None
    date_of_creation: date | None = None
    date_of_cessation: date | None = None


class CanonicalAddress(_CanonicalModel):
    """An address for a company. Mirrors `silver.company_address`.

    Covers the registered office today; `address_type` allows other
    address kinds to be added later without a schema change. Every field
    but `company_number` and `address_type` is optional — Companies House
    addresses may omit any individual line, or be empty altogether.
    """

    company_number: str
    address_type: str
    premises: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    locality: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None


class CanonicalPreviousName(_CanonicalModel):
    """A previous name a company traded under. Mirrors `silver.company_previous_name`."""

    company_number: str
    name: str
    effective_from: date | None = None
    ceased_on: date | None = None


class CanonicalSicCode(_CanonicalModel):
    """A SIC code associated with a company. Mirrors `silver.company_sic`."""

    company_number: str
    sic_code: str


class CanonicalSearchMatch(_CanonicalModel):
    """Links a search query to a company it returned. Mirrors `silver.company_search_match`."""

    query: str
    company_number: str
    retrieved_at: datetime
