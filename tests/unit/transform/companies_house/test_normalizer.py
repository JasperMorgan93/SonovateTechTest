import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.companies_house.normalizer import CompaniesHouseNormalizer

FIXTURE_PAGE = Path(__file__).parents[3] / "fixtures" / "ch_search_result_page.json"


def _bronze_dir_with_fixture_page(tmp_path: Path) -> Path:
    bronze_dir = tmp_path / "bronze" / "ch_search_result"
    bronze_dir.mkdir(parents=True)
    shutil.copy(FIXTURE_PAGE, bronze_dir / "sono_start0.json")
    return bronze_dir


def test_read_bronze_reads_every_json_file_in_the_bronze_dir(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )

    records = normalizer.read_bronze()

    assert len(records) == 1
    assert records[0]["query"] == "sono"


def test_map_to_canonical_maps_a_full_item_to_company_address_and_match(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )
    records = normalizer.read_bronze()

    companies, addresses, matches = normalizer.map_to_canonical(records)

    company = next(c for c in companies if c.company_number == "17013908")
    assert company.title == "CENSOR AI LIMITED"
    assert company.company_type == "ltd"
    assert company.company_status == "active"
    assert company.date_of_creation == date(2026, 2, 5)
    assert company.source_system == "companies_house"
    assert company.source_retrieved_at == datetime(2026, 8, 23, 11, 9, 50, 764153, tzinfo=timezone.utc)

    address = next(a for a in addresses if a.company_number == "17013908")
    assert address.address_type == "registered_office"
    assert address.premises == "74"
    assert address.locality == "London"

    match = next(m for m in matches if m.company_number == "17013908")
    assert match.query == "sono"
    assert match.retrieved_at == datetime(2026, 8, 23, 11, 9, 50, 764153, tzinfo=timezone.utc)


def test_map_to_canonical_maps_dissolved_item_with_cessation_date(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )
    records = normalizer.read_bronze()

    companies, _, _ = normalizer.map_to_canonical(records)

    company = next(c for c in companies if c.company_number == "13858388")
    assert company.company_status == "dissolved"
    assert company.date_of_creation == date(2022, 1, 19)
    assert company.date_of_cessation == date(2026, 8, 11)


def test_map_to_canonical_tolerates_item_missing_status_creation_date_and_address(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )
    records = normalizer.read_bronze()

    companies, addresses, matches = normalizer.map_to_canonical(records)

    company = next(c for c in companies if c.company_number == "CE008116")
    assert company.title == "SONO VIVO"
    assert company.company_status is None
    assert company.date_of_creation is None
    assert not any(a.company_number == "CE008116" for a in addresses)
    assert any(m.company_number == "CE008116" for m in matches)


def test_map_to_canonical_treats_non_date_cessation_value_as_absent(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )
    records = normalizer.read_bronze()

    companies, _, _ = normalizer.map_to_canonical(records)

    company = next(c for c in companies if c.company_number == "CE016346")
    assert company.company_status == "converted-closed"
    assert company.date_of_cessation is None


def test_map_to_canonical_produces_one_search_match_per_item(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )
    records = normalizer.read_bronze()

    companies, _, matches = normalizer.map_to_canonical(records)

    assert len(matches) == len(companies) == 4


def test_run_reads_bronze_and_writes_silver_end_to_end(tmp_path):
    bronze_dir = _bronze_dir_with_fixture_page(tmp_path)
    silver_dir = tmp_path / "silver"
    normalizer = CompaniesHouseNormalizer(silver_sink=FileSilverSink(base_dir=silver_dir), bronze_dir=bronze_dir)

    summary = normalizer.run()

    assert summary.companies == 4
    assert summary.addresses == 2
    assert summary.search_matches == 4
    written = json.loads((silver_dir / "company" / "17013908.json").read_text(encoding="utf-8"))
    assert written["title"] == "CENSOR AI LIMITED"
