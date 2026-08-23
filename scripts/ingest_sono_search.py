"""Fetch every reachable /search/companies result for a query and write it to bronze.

Run with: python scripts/ingest_sono_search.py

Answers Sonovate tech test Question 1 ("how many companies match 'sono'")
by reading `total_results` directly from the first page of the search.
"""

from datetime import datetime, timezone
from typing import Any

from company_data_platform.ingestion.rest.companies_house.client import CompaniesHouseClient
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
from company_data_platform.ingestion.rest.companies_house.exceptions import CompaniesHouseError
from company_data_platform.ingestion.rest.companies_house.pagination import paginate_pages_by_start_index
from company_data_platform.storage.bronze.writer import CompaniesHouseBronzeWriter

QUERY = "sono"


def ingest_search_results(
    query: str,
    client: CompaniesHouseClient,
    config: CompaniesHouseConfig,
    writer: CompaniesHouseBronzeWriter,
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
        writer.write_search_result_page(
            query=query,
            start_index=start_index,
            payload=page,
            retrieved_at=retrieved_at,
            source_url=source_url,
        )

    return total_results if total_results is not None else 0


def main() -> None:
    """Fetch and bronze-write every reachable 'sono' search result, then
    print the total count Companies House reports for the query."""
    config = CompaniesHouseConfig()
    client = CompaniesHouseClient(config)
    writer = CompaniesHouseBronzeWriter()

    try:
        total_companies = ingest_search_results(QUERY, client, config, writer)
    except CompaniesHouseError as exc:
        print(f"Ingestion failed while fetching '{QUERY}' results: {exc}")
        raise

    print(f"Companies matching '{QUERY}': {total_companies}")


if __name__ == "__main__":
    main()
