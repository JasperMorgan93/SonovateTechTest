"""Fetch every reachable /search/companies result for a query and write it to bronze.

Run with: python scripts/ingest_sono_search.py

Answers Sonovate tech test Question 1 ("how many companies match 'sono'")
by reading `total_results` directly from the first page of the search —
Companies House reports this on every page — then paginating and
writing each raw page it can safely reach to the bronze writer's
`ch_search_result/` subdirectory (see `storage/bronze/writer.py` for the
exact location). Companies House returns errors once start_index goes
beyond roughly the first 1000 results (see
docs/BDD/data_engineer_test_spec.txt), so bronze coverage may be a
prefix of the full result set for a query with more matches than that —
the reported count is still accurate because it comes from the API's
own total_results, not from how many pages were fetched.
Requires COMPANIES_HOUSE_API_KEY to be set in the environment.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from company_data_platform.ingestion.rest.companies_house.client import CompaniesHouseClient
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.ingestion.rest.companies_house.exceptions import CompaniesHouseError
from company_data_platform.ingestion.rest.companies_house.pagination import paginate_pages_by_start_index
from company_data_platform.storage.bronze.writer import BRONZE_DIR, write_search_result_page

QUERY = "sono"


def ingest_search_results(
    query: str,
    client: CompaniesHouseClient,
    config: CompaniesHouseConfig,
    base_dir: Path = BRONZE_DIR,
) -> int:
    """Fetch every reachable page of `query`'s search results, write each
    to bronze, and return the total company count reported by the API.

    Returns `total_results` from the first page (the API's own count of
    matches) rather than the number of items actually fetched — those
    can differ if Companies House's pagination ceiling is reached before
    every page has been retrieved.
    """
    items_per_page = config.default_items_per_page

    def fetch_page(start_index: int) -> dict[str, Any]:
        return client.search_companies(query, items_per_page=items_per_page, start_index=start_index)

    total_results: int | None = None

    for start_index, page in paginate_pages_by_start_index(fetch_page):
        if total_results is None:
            total_results = page.get("total_results")

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

    return total_results if total_results is not None else 0


def main() -> None:
    """Fetch and bronze-write every reachable 'sono' search result, then
    print the total count Companies House reports for the query."""
    config = CompaniesHouseConfig()
    client = CompaniesHouseClient(config)

    try:
        total_companies = ingest_search_results(QUERY, client, config)
    except CompaniesHouseError as exc:
        print(f"Ingestion failed while fetching '{QUERY}' results: {exc}")
        raise

    print(f"Companies matching '{QUERY}': {total_companies}")


if __name__ == "__main__":
    main()
