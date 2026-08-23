import json
from datetime import date, datetime, timezone

import pytest

from company_data_platform.storage.silver.base import SilverSink
from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)


def test_file_silver_sink_is_a_silver_sink(tmp_path):
    assert isinstance(FileSilverSink(base_dir=tmp_path), SilverSink)


def test_file_silver_sink_defaults_to_the_package_own_directory():
    from company_data_platform.storage.silver.file_sink import SILVER_DIR

    sink = FileSilverSink()

    assert sink._base_dir == SILVER_DIR


def test_silver_sink_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        SilverSink()


def test_write_companies_creates_one_json_file_per_company_number(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    company = CanonicalCompany(
        company_number="17013908",
        title="CENSOR AI LIMITED",
        company_type="ltd",
        company_status="active",
        date_of_creation=date(2026, 2, 5),
        source_system="companies_house",
        source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    sink.write_companies([company])

    output_path = tmp_path / "company" / "17013908.json"
    assert output_path.exists()
    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["company_number"] == "17013908"
    assert record["date_of_creation"] == "2026-02-05"


def test_write_addresses_creates_one_json_file_per_company_and_address_type(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    address = CanonicalAddress(
        company_number="17013908",
        address_type="registered_office",
        premises="74",
        locality="London",
    )

    sink.write_addresses([address])

    output_path = tmp_path / "company_address" / "17013908_registered_office.json"
    assert output_path.exists()
    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["premises"] == "74"


def test_write_search_matches_creates_one_json_file_per_query_and_company_number(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    match = CanonicalSearchMatch(
        query="sono",
        company_number="17013908",
        retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
    )

    sink.write_search_matches([match])

    output_path = tmp_path / "company_search_match" / "sono_17013908.json"
    assert output_path.exists()
    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["query"] == "sono"
    assert record["retrieved_at"] == "2026-08-23T11:09:50Z"
