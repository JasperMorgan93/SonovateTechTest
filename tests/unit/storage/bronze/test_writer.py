import json
from datetime import datetime, timezone

from company_data_platform.storage.bronze.writer import CompaniesHouseBronzeWriter


def test_write_search_result_page_creates_file_with_payload_and_metadata(tmp_path):
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)
    payload = {"items": [{"company_number": "12345678"}], "total_results": 1}
    retrieved_at = datetime(2026, 8, 22, 10, 30, 0, tzinfo=timezone.utc)

    output_path = writer.write_search_result_page(
        query="sono",
        start_index=0,
        payload=payload,
        retrieved_at=retrieved_at,
        source_url="https://api.company-information.service.gov.uk/search/companies?q=sono",
    )

    assert output_path.exists()
    assert output_path.parent == tmp_path / "ch_search_result"

    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["query"] == "sono"
    assert record["start_index"] == 0
    assert record["source_url"] == "https://api.company-information.service.gov.uk/search/companies?q=sono"
    assert record["retrieved_at"] == "2026-08-22T10:30:00+00:00"
    assert record["payload"] == payload


def test_write_search_result_page_creates_distinct_files_for_different_pages(tmp_path):
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)
    payload_page_0 = {"items": [{"company_number": "1"}], "total_results": 2}
    payload_page_1 = {"items": [{"company_number": "2"}], "total_results": 2}
    retrieved_at = datetime(2026, 8, 22, 10, 30, 0, tzinfo=timezone.utc)

    path_0 = writer.write_search_result_page(
        query="sono",
        start_index=0,
        payload=payload_page_0,
        retrieved_at=retrieved_at,
        source_url="https://example.test/search/companies?q=sono&start_index=0",
    )
    path_1 = writer.write_search_result_page(
        query="sono",
        start_index=1,
        payload=payload_page_1,
        retrieved_at=retrieved_at,
        source_url="https://example.test/search/companies?q=sono&start_index=1",
    )

    assert path_0 != path_1
    assert path_0.exists()
    assert path_1.exists()


def test_write_record_creates_file_under_subdir_of_base_dir(tmp_path):
    from company_data_platform.storage.bronze.writer import BronzeWriter

    writer = BronzeWriter(base_dir=tmp_path)

    output_path = writer.write_record("some_subdir", "some_file.json", {"key": "value"})

    assert output_path == tmp_path / "some_subdir" / "some_file.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"key": "value"}


def test_bronze_writer_defaults_to_the_package_own_directory():
    from company_data_platform.storage.bronze.writer import BRONZE_DIR, BronzeWriter

    writer = BronzeWriter()

    assert writer._base_dir == BRONZE_DIR
