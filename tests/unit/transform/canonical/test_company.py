from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalPreviousName,
    CanonicalSearchMatch,
    CanonicalSicCode,
)


def test_canonical_company_constructs_with_only_required_fields():
    company = CanonicalCompany(
        company_number="17013908",
        title="CENSOR AI LIMITED",
        company_type="ltd",
        source_system="companies_house",
        source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    assert company.company_status is None
    assert company.company_status_detail is None
    assert company.company_subtype is None
    assert company.jurisdiction is None
    assert company.date_of_creation is None
    assert company.date_of_cessation is None


def test_canonical_company_coerces_iso_date_strings_to_dates():
    company = CanonicalCompany(
        company_number="13858388",
        title="SONO MUSIC LTD",
        company_type="ltd",
        company_status="dissolved",
        date_of_creation="2022-01-19",
        date_of_cessation="2026-08-11",
        source_system="companies_house",
        source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    assert company.date_of_creation == date(2022, 1, 19)
    assert company.date_of_cessation == date(2026, 8, 11)


def test_canonical_company_missing_required_field_raises_validation_error():
    with pytest.raises(ValidationError):
        CanonicalCompany(
            title="CENSOR AI LIMITED",
            company_type="ltd",
            source_system="companies_house",
            source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
        )


def test_canonical_company_is_immutable():
    company = CanonicalCompany(
        company_number="17013908",
        title="CENSOR AI LIMITED",
        company_type="ltd",
        source_system="companies_house",
        source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    with pytest.raises(ValidationError):
        company.title = "SOMETHING ELSE"


def test_canonical_address_allows_all_fields_except_company_number_and_type_to_be_absent():
    address = CanonicalAddress(
        company_number="CE008116",
        address_type="registered_office",
    )

    assert address.premises is None
    assert address.address_line_1 is None
    assert address.address_line_2 is None
    assert address.locality is None
    assert address.region is None
    assert address.postal_code is None
    assert address.country is None


def test_canonical_address_missing_company_number_raises_validation_error():
    with pytest.raises(ValidationError):
        CanonicalAddress(address_type="registered_office")


def test_canonical_previous_name_requires_company_number_and_name():
    with pytest.raises(ValidationError):
        CanonicalPreviousName(company_number="17013908")


def test_canonical_previous_name_constructs_with_optional_dates_absent():
    previous_name = CanonicalPreviousName(company_number="17013908", name="OLD NAME LTD")

    assert previous_name.effective_from is None
    assert previous_name.ceased_on is None


def test_canonical_sic_code_requires_company_number_and_sic_code():
    with pytest.raises(ValidationError):
        CanonicalSicCode(company_number="17013908")


def test_canonical_sic_code_constructs_with_required_fields():
    sic_code = CanonicalSicCode(company_number="17013908", sic_code="62012")

    assert sic_code.sic_code == "62012"


def test_canonical_search_match_requires_query_company_number_and_retrieved_at():
    with pytest.raises(ValidationError):
        CanonicalSearchMatch(query="sono", company_number="17013908")


def test_canonical_search_match_constructs_with_required_fields():
    match = CanonicalSearchMatch(
        query="sono",
        company_number="17013908",
        retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    assert match.query == "sono"
    assert match.company_number == "17013908"
