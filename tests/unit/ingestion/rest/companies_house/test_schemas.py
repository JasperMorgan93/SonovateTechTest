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
