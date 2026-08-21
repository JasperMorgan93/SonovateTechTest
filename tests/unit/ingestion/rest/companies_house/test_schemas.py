from datetime import date

import pytest
from pydantic import ValidationError

from company_data_platform.ingestion.rest.companies_house.schemas import (
    Address,
    CompanyProfile,
    PreviousCompanyName,
    SearchCompaniesResponse,
    SearchResultItem,
)


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


def test_search_result_item_requires_company_number():
    with pytest.raises(ValidationError):
        SearchResultItem.model_validate({"title": "SONOVATE LIMITED"})


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


def test_company_profile_accepts_company_type_by_field_name_too():
    # populate_by_name=True means code constructing a CompanyProfile
    # directly (e.g. in a future test fixture) can use the attribute
    # name, not just the raw API's `type` alias.
    profile = CompanyProfile(company_number="00000009", company_status="active", company_type="ltd")

    assert profile.company_type == "ltd"


def test_company_profile_requires_company_number():
    with pytest.raises(ValidationError):
        CompanyProfile.model_validate({"company_status": "active"})
