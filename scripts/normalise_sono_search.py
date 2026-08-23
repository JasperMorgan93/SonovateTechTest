"""Read every 'sono' search-result bronze page and map it into the silver layer.

Run with: python scripts/normalise_sono_search.py

Reads `storage/bronze/ch_search_result/` and writes canonical companies,
addresses, and search matches to `storage/silver/` (see
`transform/companies_house/normalizer.py`). Assumes
`scripts/ingest_sono_search.py` has already populated bronze.
"""

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.base import Normalizer, RunSummary
from company_data_platform.transform.companies_house.normalizer import CompaniesHouseNormalizer


def normalise_search_results(normalizer: Normalizer) -> RunSummary:
    """Run a normalizer's full bronze-to-silver pipeline and return its summary."""
    return normalizer.run()


def main() -> None:
    """Normalise every 'sono' search-result bronze page into silver, then print a summary."""
    silver_sink = FileSilverSink()
    normalizer = CompaniesHouseNormalizer(silver_sink=silver_sink)

    summary = normalise_search_results(normalizer)

    print(" SONO SEARCH NORMALISATION COMPLETE ")
    print("---")
    print(f"Silver files written to: {silver_sink._base_dir}")
    print("---")
    print(f"Companies: {summary.companies}")
    print(f"Addresses: {summary.addresses}")
    print(f"Search matches: {summary.search_matches}")


if __name__ == "__main__":
    main()
