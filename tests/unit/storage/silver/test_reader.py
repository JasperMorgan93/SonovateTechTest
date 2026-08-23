from datetime import date, datetime, timezone

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.storage.silver.reader import read_addresses, read_companies, read_search_matches
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)


def test_read_companies_returns_every_written_company(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    sink.write_companies(
        [
            CanonicalCompany(
                company_number="1",
                title="SONO ONE LTD",
                company_type="ltd",
                company_status="active",
                source_system="companies_house",
                source_retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
            )
        ]
    )

    records = read_companies(tmp_path)

    assert len(records) == 1
    assert records[0]["company_number"] == "1"


def test_read_addresses_returns_every_written_address(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    sink.write_addresses(
        [CanonicalAddress(company_number="1", address_type="registered_office", premises="6-8")]
    )

    records = read_addresses(tmp_path)

    assert len(records) == 1
    assert records[0]["premises"] == "6-8"


def test_read_search_matches_returns_every_written_match(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    sink.write_search_matches(
        [CanonicalSearchMatch(query="sono", company_number="1", retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc))]
    )

    records = read_search_matches(tmp_path)

    assert len(records) == 1
    assert records[0]["query"] == "sono"


def test_read_companies_returns_empty_list_when_silver_directory_does_not_exist(tmp_path):
    assert read_companies(tmp_path / "does_not_exist") == []
