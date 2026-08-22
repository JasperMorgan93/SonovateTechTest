"""Fetch every /search/companies result for a query and write it to bronze.

Run with: python scripts/ingest_sono_search.py

Answers Sonovate tech test Question 1 ("how many companies match 'sono'")
by fetching every page of the search, writing each raw page to the
bronze writer's `ch_search_result/` subdirectory (see
`storage/bronze/writer.py` for the exact location), and printing the
total company count.
Requires COMPANIES_HOUSE_API_KEY to be set in the environment.
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from company_data_platform.ingestion.rest.companies_house.client import CompaniesHouseClient
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.ingestion.rest.companies_house.pagination import paginate_pages_by_start_index
from company_data_platform.storage.bronze.writer import BRONZE_DIR, write_search_result_page

QUERY = "sono"


def ingest_search_results(
    query: str,
    client: CompaniesHouseClient,
    config: CompaniesHouseConfig,
    base_dir: Path = BRONZE_DIR,
) -> int:
    """Fetch every page of `query`'s search results, write each to bronze,
    and return the total number of companies found."""
    items_per_page = config.default_items_per_page

    def fetch_page(start_index: int) -> dict[str, Any]:
        return client.search_companies(query, items_per_page=items_per_page, start_index=start_index)

    total_companies = 0
    for start_index, page in _enumerate_by_actual_page_size(
        paginate_pages_by_start_index(fetch_page, items_per_page)
    ):
        items = page["items"]
        retrieved_at = datetime.now(timezone.utc)
        source_url = (
            f"{config.base_url}{config.search_companies_path}"
            f"?q={query}&items_per_page={items_per_page}&start_index={start_index}"
        )
        write_search_result_page(
            query=query,
            start_index=start_index,
            payload=page,
            retrieved_at=retrieved_at,
            source_url=source_url,
            base_dir=base_dir,
        )
        total_companies += len(items)

    return total_companies


def _enumerate_by_actual_page_size(pages: Iterator[dict[str, Any]]) -> Iterator[tuple[int, dict[str, Any]]]:
    """Pair each page with the start_index it was actually fetched at.

    `paginate_pages_by_start_index` doesn't expose start_index directly
    (it only yields pages), but bronze filenames and the recorded
    source_url both need it — this reconstructs it the same way the
    paginator itself advances: by the number of items in each preceding
    page, not by a fixed page size.
    """
    start_index = 0
    for page in pages:
        yield start_index, page
        start_index += len(page.get("items", []))


def main() -> None:
    """Fetch and bronze-write every 'sono' search result, then print the total count."""
    config = CompaniesHouseConfig()
    client = CompaniesHouseClient(config)

    total_companies = ingest_search_results(QUERY, client, config)

    print(f"Companies matching '{QUERY}': {total_companies}")


if __name__ == "__main__":
    main()
