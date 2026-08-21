# Companies House Endpoint Schemas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Model the response shapes of the two Companies House "companies" endpoints (`/search/companies` and `/company/{company_number}`) as tolerant Pydantic schemas — the first concrete piece of the generic ingestion layer already designed in this repo.

**Architecture:** This repo has no code yet, only a checked-in architectural spec (`docs/architecture.md`, `docs/data-model.md`) and empty package skeletons. This plan fills in exactly one file — `ingestion/rest/companies_house/schemas.py` — plus the minimal `pyproject.toml` needed to install Pydantic and run tests. No HTTP client, no auth, no rate limiting/retry, no database, no persistence — those are separate, later slices per `docs/architecture.md` §5/§7.3. Every model tolerates unknown/missing fields, per the repo-wide rule that Companies House's schema can drift without breaking ingestion.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest.

**Spec:** [docs/architecture.md](../../architecture.md) (§5 component breakdown, §7.3 Companies House specifics), [docs/data-model.md](../../data-model.md) (field-to-question mapping — confirms which fields are actually needed downstream).

## Global Constraints

- **Tolerate schema drift:** every model uses `model_config = ConfigDict(extra="ignore")`; no field is asserted to always be present unless Companies House guarantees it structurally (only `company_number` on both a search item and a profile, and `company_status` on a profile).
- **Company number is identity:** never model company name/title as a key field; `company_number` is always `str`, never optional, on any model that represents a company.
- **Type hints & Google-style docstrings** on every public class (coding-principles.md).
- **No magic literals:** no repeated field-name strings outside the model definitions themselves.
- **This slice does not touch:** `client.py`, `auth.py`, `exceptions.py`, `config.py`, `storage/`, `pipeline.py`, `cli.py`. Do not create them.

---

### Task 1: Project scaffolding (pyproject.toml, installable package, pytest runs)

**Files:**
- Create: `pyproject.toml`
- Test: none (verification is that `pytest` runs cleanly with zero tests)

**Interfaces:**
- Consumes: nothing
- Produces: an installable `company_data_platform` package (editable install) and a working `pytest` invocation that later tasks' tests run under. Package root is `src/company_data_platform` (already exists with `__init__.py` files).

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "company-data-platform"
version = "0.1.0"
description = "Sonovate tech test: Companies House data platform"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7,<3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Install the package in editable mode with dev dependencies**

Run: `pip install -e ".[dev]"`
Expected: installs successfully, `pydantic` and `pytest` importable.

- [ ] **Step 3: Verify pytest runs with no tests yet**

Run: `pytest`
Expected: `no tests ran` (exit code 5) or a clean collection of the existing `.gitkeep`-only directories — not an import or config error.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml with pydantic/pytest dependencies"
```

---

### Task 2: `Address` model

**Files:**
- Create: `src/company_data_platform/ingestion/rest/companies_house/schemas.py`
- Test: `tests/unit/ingestion/rest/companies_house/test_schemas.py`

**Interfaces:**
- Consumes: nothing
- Produces: `Address` — used by `SearchResultItem.address` (Task 4) and `CompanyProfile.registered_office_address` (Task 5). Fields: `premises: str | None`, `address_line_1: str | None`, `address_line_2: str | None`, `locality: str | None`, `region: str | None`, `postal_code: str | None`, `country: str | None`. All default `None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/ingestion/rest/companies_house/test_schemas.py
from company_data_platform.ingestion.rest.companies_house.schemas import Address


def test_address_parses_full_payload():
    payload = {
        "premises": "14B",
        "address_line_1": "Example Street",
        "address_line_2": "Suite 2",
        "locality": "London",
        "region": "Greater London",
        "postal_code": "EC1A 1AA",
        "country": "United Kingdom",
    }

    address = Address.model_validate(payload)

    assert address.premises == "14B"
    assert address.address_line_1 == "Example Street"
    assert address.address_line_2 == "Suite 2"
    assert address.locality == "London"
    assert address.region == "Greater London"
    assert address.postal_code == "EC1A 1AA"
    assert address.country == "United Kingdom"


def test_address_tolerates_missing_optional_fields():
    payload = {"premises": "6-8", "locality": "Leeds"}

    address = Address.model_validate(payload)

    assert address.premises == "6-8"
    assert address.locality == "Leeds"
    assert address.address_line_1 is None
    assert address.postal_code is None


def test_address_ignores_unknown_fields():
    payload = {"premises": "1", "some_new_field_ch_adds_later": "value"}

    address = Address.model_validate(payload)

    assert address.premises == "1"
    assert not hasattr(address, "some_new_field_ch_adds_later")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: FAIL — `ModuleNotFoundError` or `ImportError: cannot import name 'Address'` (module doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# src/company_data_platform/ingestion/rest/companies_house/schemas.py
"""Tolerant Pydantic models for Companies House REST response payloads.

Every model here accepts and silently drops unknown fields, and treats
every field Companies House does not structurally guarantee as optional.
This is deliberate: the upstream schema is documented as subject to
change, and ingestion must not break when a new field appears or an
optional one is absent.
"""

from pydantic import BaseModel, ConfigDict


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/company_data_platform/ingestion/rest/companies_house/schemas.py tests/unit/ingestion/rest/companies_house/test_schemas.py
git commit -m "feat: add Address schema for Companies House payloads"
```

---

### Task 3: `PreviousCompanyName` model

**Files:**
- Modify: `src/company_data_platform/ingestion/rest/companies_house/schemas.py`
- Test: `tests/unit/ingestion/rest/companies_house/test_schemas.py`

**Interfaces:**
- Consumes: nothing (standalone model)
- Produces: `PreviousCompanyName` — used by `CompanyProfile.previous_company_names` (Task 5). Fields: `name: str | None`, `effective_from: date | None`, `ceased_on: date | None`. All default `None`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/unit/ingestion/rest/companies_house/test_schemas.py
from datetime import date

from company_data_platform.ingestion.rest.companies_house.schemas import (
    Address,
    PreviousCompanyName,
)


def test_previous_company_name_parses_full_payload():
    payload = {
        "name": "OLD NAME LIMITED",
        "effective_from": "2015-01-01",
        "ceased_on": "2019-06-30",
    }

    previous_name = PreviousCompanyName.model_validate(payload)

    assert previous_name.name == "OLD NAME LIMITED"
    assert previous_name.effective_from == date(2015, 1, 1)
    assert previous_name.ceased_on == date(2019, 6, 30)


def test_previous_company_name_tolerates_missing_dates():
    payload = {"name": "ANOTHER OLD NAME LTD"}

    previous_name = PreviousCompanyName.model_validate(payload)

    assert previous_name.name == "ANOTHER OLD NAME LTD"
    assert previous_name.effective_from is None
    assert previous_name.ceased_on is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: FAIL — `ImportError: cannot import name 'PreviousCompanyName'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/company_data_platform/ingestion/rest/companies_house/schemas.py
from datetime import date


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
```

(Add the `from datetime import date` import once, near the top of the file, alongside the existing `pydantic` import.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: PASS (5 tests total)

- [ ] **Step 5: Commit**

```bash
git add src/company_data_platform/ingestion/rest/companies_house/schemas.py tests/unit/ingestion/rest/companies_house/test_schemas.py
git commit -m "feat: add PreviousCompanyName schema"
```

---

### Task 4: `SearchResultItem` and `SearchCompaniesResponse` models

**Files:**
- Modify: `src/company_data_platform/ingestion/rest/companies_house/schemas.py`
- Test: `tests/unit/ingestion/rest/companies_house/test_schemas.py`

**Interfaces:**
- Consumes: `Address` (Task 2)
- Produces: `SearchResultItem` (fields: `company_number: str`, `title: str | None`, `company_type: str | None`, `company_status: str | None`, `date_of_creation: date | None`, `date_of_cessation: date | None`, `address: Address | None`, `description: str | None`, `kind: str | None`) and `SearchCompaniesResponse` (fields: `items: list[SearchResultItem]` default `[]`, `items_per_page: int | None`, `start_index: int | None`, `total_results: int | None`, `kind: str | None`). These are the models a later `client.py` task will use as the return type of `search_companies()`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/unit/ingestion/rest/companies_house/test_schemas.py
from company_data_platform.ingestion.rest.companies_house.schemas import (
    SearchCompaniesResponse,
    SearchResultItem,
)


def test_search_result_item_parses_full_payload():
    payload = {
        "company_number": "12345678",
        "title": "SONOVATE LIMITED",
        "company_type": "ltd",
        "company_status": "active",
        "date_of_creation": "2016-03-14",
        "date_of_cessation": None,
        "address": {"premises": "1", "locality": "London"},
        "description": "12345678 - incorporated on 14 March 2016",
        "kind": "search-results#company",
    }

    item = SearchResultItem.model_validate(payload)

    assert item.company_number == "12345678"
    assert item.title == "SONOVATE LIMITED"
    assert item.company_status == "active"
    assert item.date_of_creation == date(2016, 3, 14)
    assert item.date_of_cessation is None
    assert item.address is not None
    assert item.address.locality == "London"


def test_search_result_item_requires_only_company_number():
    payload = {"company_number": "00000006"}

    item = SearchResultItem.model_validate(payload)

    assert item.company_number == "00000006"
    assert item.title is None
    assert item.address is None


def test_search_companies_response_parses_multi_item_page():
    payload = {
        "items": [
            {"company_number": "11111111", "title": "SONOVATE ONE LTD"},
            {"company_number": "22222222", "title": "SONOVATE TWO LTD"},
        ],
        "items_per_page": 20,
        "start_index": 0,
        "total_results": 2,
        "kind": "search#companies",
    }

    response = SearchCompaniesResponse.model_validate(payload)

    assert response.total_results == 2
    assert len(response.items) == 2
    assert response.items[0].company_number == "11111111"
    assert response.items[1].title == "SONOVATE TWO LTD"


def test_search_companies_response_tolerates_zero_results():
    payload = {"items": [], "items_per_page": 20, "start_index": 0, "total_results": 0}

    response = SearchCompaniesResponse.model_validate(payload)

    assert response.items == []
    assert response.total_results == 0


def test_search_companies_response_ignores_unknown_top_level_field():
    payload = {
        "items": [{"company_number": "33333333"}],
        "total_results": 1,
        "a_field_ch_adds_later": {"nested": "value"},
    }

    response = SearchCompaniesResponse.model_validate(payload)

    assert response.items[0].company_number == "33333333"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: FAIL — `ImportError: cannot import name 'SearchResultItem'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/company_data_platform/ingestion/rest/companies_house/schemas.py

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: PASS (10 tests total)

- [ ] **Step 5: Commit**

```bash
git add src/company_data_platform/ingestion/rest/companies_house/schemas.py tests/unit/ingestion/rest/companies_house/test_schemas.py
git commit -m "feat: add SearchResultItem and SearchCompaniesResponse schemas"
```

---

### Task 5: `CompanyProfile` model

**Files:**
- Modify: `src/company_data_platform/ingestion/rest/companies_house/schemas.py`
- Test: `tests/unit/ingestion/rest/companies_house/test_schemas.py`

**Interfaces:**
- Consumes: `Address` (Task 2), `PreviousCompanyName` (Task 3)
- Produces: `CompanyProfile` — the model a later `client.py` task's `get_company()` will return. Fields: `company_number: str`, `company_name: str | None`, `company_status: str`, `company_status_detail: str | None`, `company_type: str | None` (populated from the raw `type` field — see note below), `company_subtype: str | None`, `jurisdiction: str | None`, `date_of_creation: date | None`, `date_of_cessation: date | None`, `registered_office_address: Address | None`, `sic_codes: list[str]` default `[]`, `previous_company_names: list[PreviousCompanyName]` default `[]`.

**Note on `type` vs `company_type`:** Companies House is inconsistent between endpoints — `/search/companies` items use the field name `company_type` (Task 4), but `/company/{company_number}` profiles use plain `type` for the same concept. This schema exposes both as `company_type` on their respective models for a consistent attribute name across the platform, using a Pydantic validation alias on `CompanyProfile` to read the raw `type` key.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/unit/ingestion/rest/companies_house/test_schemas.py
from company_data_platform.ingestion.rest.companies_house.schemas import CompanyProfile


def test_company_profile_parses_full_active_company():
    payload = {
        "company_number": "12345678",
        "company_name": "SONOVATE LIMITED",
        "company_status": "active",
        "company_status_detail": None,
        "type": "ltd",
        "company_subtype": None,
        "jurisdiction": "england-wales",
        "date_of_creation": "2016-03-14",
        "date_of_cessation": None,
        "registered_office_address": {
            "premises": "1",
            "address_line_1": "Example Street",
            "locality": "London",
            "postal_code": "EC1A 1AA",
            "country": "United Kingdom",
        },
        "sic_codes": ["62012", "62020"],
        "previous_company_names": [
            {"name": "OLD NAME LIMITED", "effective_from": "2015-01-01", "ceased_on": "2016-03-14"}
        ],
    }

    profile = CompanyProfile.model_validate(payload)

    assert profile.company_number == "12345678"
    assert profile.company_name == "SONOVATE LIMITED"
    assert profile.company_status == "active"
    assert profile.company_type == "ltd"
    assert profile.jurisdiction == "england-wales"
    assert profile.date_of_creation == date(2016, 3, 14)
    assert profile.registered_office_address is not None
    assert profile.registered_office_address.postal_code == "EC1A 1AA"
    assert profile.sic_codes == ["62012", "62020"]
    assert len(profile.previous_company_names) == 1
    assert profile.previous_company_names[0].name == "OLD NAME LIMITED"


def test_company_profile_parses_dissolved_company_with_cessation_date():
    payload = {
        "company_number": "00000006",
        "company_status": "dissolved",
        "date_of_creation": "1900-01-01",
        "date_of_cessation": "1990-12-31",
    }

    profile = CompanyProfile.model_validate(payload)

    assert profile.company_status == "dissolved"
    assert profile.date_of_cessation == date(1990, 12, 31)


def test_company_profile_tolerates_missing_optional_collections_and_fields():
    payload = {"company_number": "00000007", "company_status": "active"}

    profile = CompanyProfile.model_validate(payload)

    assert profile.company_name is None
    assert profile.company_subtype is None
    assert profile.company_type is None
    assert profile.registered_office_address is None
    assert profile.sic_codes == []
    assert profile.previous_company_names == []


def test_company_profile_ignores_unknown_fields():
    payload = {
        "company_number": "00000008",
        "company_status": "active",
        "accounts": {"next_due": "2027-01-01"},
        "confirmation_statement": {"next_due": "2027-02-01"},
    }

    profile = CompanyProfile.model_validate(payload)

    assert profile.company_number == "00000008"
    assert not hasattr(profile, "accounts")


def test_company_profile_accepts_company_type_by_field_name_too():
    # populate_by_name=True means code constructing a CompanyProfile
    # directly (e.g. in a future test fixture) can use the attribute
    # name, not just the raw API's `type` alias.
    profile = CompanyProfile(company_number="00000009", company_status="active", company_type="ltd")

    assert profile.company_type == "ltd"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: FAIL — `ImportError: cannot import name 'CompanyProfile'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to src/company_data_platform/ingestion/rest/companies_house/schemas.py
from pydantic import Field


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
```

(Move the `from pydantic import Field` import up to the single `pydantic` import line at the top of the file alongside `BaseModel` and `ConfigDict`, rather than repeating it — i.e. `from pydantic import BaseModel, ConfigDict, Field`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/ingestion/rest/companies_house/test_schemas.py -v`
Expected: PASS (15 tests total)

- [ ] **Step 5: Commit**

```bash
git add src/company_data_platform/ingestion/rest/companies_house/schemas.py tests/unit/ingestion/rest/companies_house/test_schemas.py
git commit -m "feat: add CompanyProfile schema"
```

---

### Task 6: Full suite verification

**Files:** none created or modified — verification only.

**Interfaces:**
- Consumes: everything from Tasks 1-5.
- Produces: confirmation the slice is complete and self-consistent.

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: all 15 tests in `tests/unit/ingestion/rest/companies_house/test_schemas.py` PASS, nothing else collected fails.

- [ ] **Step 2: Confirm no unused imports or dead code**

Open `src/company_data_platform/ingestion/rest/companies_house/schemas.py` and check every imported name (`BaseModel`, `ConfigDict`, `Field`, `date`) is used, and every model defined (`Address`, `PreviousCompanyName`, `SearchResultItem`, `SearchCompaniesResponse`, `CompanyProfile`) has at least one test exercising it. No step needed if the review passes; fix and re-run Step 1 if not.

- [ ] **Step 3: Commit if any cleanup was needed**

```bash
git add -A
git commit -m "chore: cleanup pass on companies house schemas"
```

(Skip this commit if Step 2 found nothing to change.)
