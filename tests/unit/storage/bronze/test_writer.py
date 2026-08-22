import json
from datetime import datetime, timezone

from company_data_platform.storage.bronze.writer import write_search_result_page


def test_write_search_result_page_creates_file_with_payload_and_metadata(tmp_path):
    payload = {"items": [{"company_number": "12345678"}], "total_results": 1}
    retrieved_at = datetime(2026, 8, 22, 10, 30, 0, tzinfo=timezone.utc)

    output_path = write_search_result_page(
        query="sono",
        start_index=0,
        payload=payload,
        retrieved_at=retrieved_at,
        source_url="https://api.company-information.service.gov.uk/search/companies?q=sono",
        base_dir=tmp_path,
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
    payload_page_0 = {"items": [{"company_number": "1"}], "total_results": 2}
    payload_page_1 = {"items": [{"company_number": "2"}], "total_results": 2}
    retrieved_at = datetime(2026, 8, 22, 10, 30, 0, tzinfo=timezone.utc)

    path_0 = write_search_result_page(
        query="sono",
        start_index=0,
        payload=payload_page_0,
        retrieved_at=retrieved_at,
        source_url="https://example.test/search/companies?q=sono&start_index=0",
        base_dir=tmp_path,
    )
    path_1 = write_search_result_page(
        query="sono",
        start_index=1,
        payload=payload_page_1,
        retrieved_at=retrieved_at,
        source_url="https://example.test/search/companies?q=sono&start_index=1",
        base_dir=tmp_path,
    )

    assert path_0 != path_1
    assert path_0.exists()
    assert path_1.exists()
