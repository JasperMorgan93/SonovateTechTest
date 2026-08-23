import json

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.companies_house.normalizer import CompaniesHouseNormalizer
from scripts.normalise_sono_search import normalise_search_results


def _write_bronze_page(bronze_dir, filename: str) -> None:
    bronze_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "query": "sono",
        "start_index": 0,
        "source_url": "https://example.test/search/companies?q=sono",
        "retrieved_at": "2026-08-23T11:09:50.764153+00:00",
        "payload": {
            "items": [
                {"company_number": "1", "title": "SONO ONE LTD", "company_type": "ltd", "company_status": "active"}
            ]
        },
    }
    (bronze_dir / filename).write_text(json.dumps(record), encoding="utf-8")


def test_normalise_search_results_reads_bronze_and_writes_silver(tmp_path):
    bronze_dir = tmp_path / "bronze"
    _write_bronze_page(bronze_dir, "sono_start0.json")
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )

    summary = normalise_search_results(normalizer)

    assert summary.companies == 1
    assert (tmp_path / "silver" / "company" / "1.json").exists()


def test_normalise_search_results_returns_zero_counts_for_empty_bronze(tmp_path):
    bronze_dir = tmp_path / "bronze"
    bronze_dir.mkdir()
    normalizer = CompaniesHouseNormalizer(
        silver_sink=FileSilverSink(base_dir=tmp_path / "silver"), bronze_dir=bronze_dir
    )

    summary = normalise_search_results(normalizer)

    assert summary.companies == 0
    assert summary.addresses == 0
    assert summary.search_matches == 0
