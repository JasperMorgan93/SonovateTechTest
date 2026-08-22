"""Fetch every /search/companies result for a query and write it to bronze.

Run with: python scripts/ingest_sono_search.py

Answers Sonovate tech test Question 1 ("how many companies match 'sono'")
by fetching every page of the search, writing each raw page to
storage/bronze/ch_search_result/, and printing the total company count.
Requires COMPANIES_HOUSE_API_KEY to be set in the environment.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from company_data_platform.ingestion.rest.companies_house.client import CompaniesHouseClient
from company_data_platform.ingestion.rest.companies_house.config import CompaniesHouseConfig
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
    start_index = 0
    total_companies = 0

    while True:
        page: dict[str, Any] = client.search_companies(query, start_index=start_index)
        items = page.get("items", [])
        if not items:
            break

        retrieved_at = datetime.now(timezone.utc)
        source_url = f"{config.base_url}{config.search_companies_path}?q={query}&start_index={start_index}"
        write_search_result_page(
            query=query,
            start_index=start_index,
            payload=page,
            retrieved_at=retrieved_at,
            source_url=source_url,
            base_dir=base_dir,
        )

        total_companies += len(items)
        start_index += len(items)

        total_results = page.get("total_results")
        if total_results is not None and start_index >= total_results:
            break

    return total_companies


def main() -> None:
    config = CompaniesHouseConfig()
    client = CompaniesHouseClient(config)

    total_companies = ingest_search_results(QUERY, client, config)

    print(f"Companies matching '{QUERY}': {total_companies}")


if __name__ == "__main__":
    main()
