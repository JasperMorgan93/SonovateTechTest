"""Maps Companies House bronze search-result pages to the canonical schema.

Source is `bronze.ch_search_result` (the only bronze this platform
populates today — see `docs/architecture.md` §8). Search items carry
enough fields to answer the six test questions directly (status, type,
dates, address), so this mapper doesn't wait on a company-profile bronze
that doesn't exist yet. Fields a search item never carries
(`company_status_detail`, `company_subtype`, `jurisdiction`, previous
names, SIC codes) are simply left unset on the canonical model rather than
guessed at — a future profile-based mapper can fill them without a schema
change.

Mapping is defensive by design (`.get(...)`, never assumed keys): real
Companies House search results include items with no `company_status` or
`date_of_creation` at all (externally-registered organisations), and
addresses that are entirely empty — see the `CE008116` case in
`tests/fixtures/ch_search_result_page.json`.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from company_data_platform.storage.bronze.writer import BRONZE_DIR, SEARCH_RESULT_SUBDIR
from company_data_platform.storage.silver.base import SilverSink
from company_data_platform.transform.base import CanonicalBatch, Normalizer
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)

SOURCE_SYSTEM = "companies_house"
REGISTERED_OFFICE_ADDRESS_TYPE = "registered_office"


def _parse_optional_date(value: str | None) -> date | None:
    """Parse an ISO date string, or return `None` if absent or not a real date.

    Companies House search results have been observed to use non-date sentinel
    values here (e.g. `date_of_cessation: "Unknown"` on converted/closed
    organisations) — schema drift the guide warns to tolerate, not a value
    worth failing the whole mapping over.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _map_item_to_company(item: dict[str, Any], retrieved_at: datetime) -> CanonicalCompany:
    """Map one search-result item to a `CanonicalCompany`."""
    return CanonicalCompany(
        company_number=item["company_number"],
        title=item["title"],
        company_type=item["company_type"],
        company_status=item.get("company_status"),
        date_of_creation=_parse_optional_date(item.get("date_of_creation")),
        date_of_cessation=_parse_optional_date(item.get("date_of_cessation")),
        source_system=SOURCE_SYSTEM,
        source_retrieved_at=retrieved_at,
    )


def _map_item_to_address(item: dict[str, Any]) -> CanonicalAddress | None:
    """Map one search-result item's address to a `CanonicalAddress`, or `None` if it has none."""
    address = item.get("address") or {}
    if not address:
        return None
    return CanonicalAddress(
        company_number=item["company_number"],
        address_type=REGISTERED_OFFICE_ADDRESS_TYPE,
        premises=address.get("premises"),
        address_line_1=address.get("address_line_1"),
        address_line_2=address.get("address_line_2"),
        locality=address.get("locality"),
        region=address.get("region"),
        postal_code=address.get("postal_code"),
        country=address.get("country"),
    )


class CompaniesHouseNormalizer(Normalizer):
    """Normalizer for Companies House search-result bronze pages."""

    def __init__(self, silver_sink: SilverSink, bronze_dir: Path = BRONZE_DIR / SEARCH_RESULT_SUBDIR) -> None:
        super().__init__(silver_sink)
        self._bronze_dir = bronze_dir

    def read_bronze(self) -> list[dict[str, Any]]:
        """Read every bronze search-result page JSON file, in filename order."""
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self._bronze_dir.glob("*.json"))]

    def map_to_canonical(self, records: list[dict[str, Any]]) -> CanonicalBatch:
        """Map bronze search-result pages to canonical companies, addresses, and search matches."""
        companies: list[CanonicalCompany] = []
        addresses: list[CanonicalAddress] = []
        matches: list[CanonicalSearchMatch] = []

        for record in records:
            query = record["query"]
            retrieved_at = datetime.fromisoformat(record["retrieved_at"])
            for item in record.get("payload", {}).get("items", []):
                company = _map_item_to_company(item, retrieved_at)
                companies.append(company)

                address = _map_item_to_address(item)
                if address is not None:
                    addresses.append(address)

                matches.append(
                    CanonicalSearchMatch(
                        query=query, company_number=company.company_number, retrieved_at=retrieved_at
                    )
                )

        return companies, addresses, matches
