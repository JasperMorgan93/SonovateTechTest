from datetime import date

from company_data_platform.ingestion.rest.companies_house.schemas import (
    Address,
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


def test_address_ignores_unknown_fields():
    payload = {"premises": "1", "some_new_field_ch_adds_later": "value"}

    address = Address.model_validate(payload)

    assert address.premises == "1"
    assert not hasattr(address, "some_new_field_ch_adds_later")


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


def test_search_companies_response_ignores_unknown_top_level_field():
    payload = {
        "items": [{"company_number": "33333333"}],
        "total_results": 1,
        "a_field_ch_adds_later": {"nested": "value"},
    }

    response = SearchCompaniesResponse.model_validate(payload)

    assert response.items[0].company_number == "33333333"
