from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.storage.bronze.writer import CompaniesHouseBronzeWriter
from scripts.ingest_sono_search import ingest_search_results


class _StubClient:
    """A duck-typed stand-in for CompaniesHouseClient: only search_companies
    is exercised by ingest_search_results, so only it needs implementing."""

    def __init__(self, pages: dict[int, dict]) -> None:
        self._pages = pages

    def search_companies(self, query: str, *, start_index: int = 0, items_per_page: int | None = None) -> dict:
        return self._pages[start_index]


def test_ingest_search_results_writes_every_page_and_returns_total_count(tmp_path):
    pages = {
        0: {"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 3},
        2: {"items": [{"company_number": "3"}], "total_results": 3},
    }
    client = _StubClient(pages)
    config = CompaniesHouseConfig(api_key="test-key")
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)

    total = ingest_search_results("sono", client, config, writer)

    assert total == 3
    written_files = list((tmp_path / "ch_search_result").glob("sono_*.json"))
    assert len(written_files) == 2


def test_ingest_search_results_stops_on_empty_page_and_writes_nothing(tmp_path):
    pages = {0: {"items": [], "total_results": 0}}
    client = _StubClient(pages)
    config = CompaniesHouseConfig(api_key="test-key")
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)

    total = ingest_search_results("sono", client, config, writer)

    assert total == 0
    assert not (tmp_path / "ch_search_result").exists()


def test_ingest_search_results_advances_by_actual_page_size_not_requested_size(tmp_path):
    pages = {
        0: {"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 4},
        2: {"items": [{"company_number": "3"}, {"company_number": "4"}], "total_results": 4},
    }
    client = _StubClient(pages)
    config = CompaniesHouseConfig(api_key="test-key")
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)

    total = ingest_search_results("sono", client, config, writer)

    assert total == 4


def test_ingest_search_results_reports_total_results_not_fetched_count(tmp_path, monkeypatch):
    from company_data_platform.ingestion.rest.companies_house import pagination as pagination_module

    monkeypatch.setattr(pagination_module, "MAX_START_INDEX", 2)

    pages = {
        0: {"items": [{"company_number": "1"}], "total_results": 5000},
        1: {"items": [{"company_number": "2"}], "total_results": 5000},
    }
    client = _StubClient(pages)
    config = CompaniesHouseConfig(api_key="test-key")
    writer = CompaniesHouseBronzeWriter(base_dir=tmp_path)

    total = ingest_search_results("sono", client, config, writer)

    assert total == 5000
    written_files = list((tmp_path / "ch_search_result").glob("sono_*.json"))
    assert len(written_files) == 2
