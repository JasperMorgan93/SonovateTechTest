"""File-based `SilverSink` — a deliberate simplification for this first slice.

Mirrors `storage/bronze/writer.py`'s file-based approach: one JSON file per
canonical record, named by its natural key so a re-run overwrites rather
than duplicates. This is a stand-in for the Postgres-backed `silver.*`
design in `docs/data-model.md`, not a general-purpose data store.
"""

from collections.abc import Sequence
from pathlib import Path

from company_data_platform.storage.json_file import write_json_record
from company_data_platform.storage.silver.base import SilverSink
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)

_COMPANY_SUBDIR = "company"
_ADDRESS_SUBDIR = "company_address"
_SEARCH_MATCH_SUBDIR = "company_search_match"


class FileSilverSink(SilverSink):
    """Writes canonical records to `<base_dir>/<entity>/<natural_key>.json`."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def write_companies(self, companies: Sequence[CanonicalCompany]) -> None:
        """Write one file per company, named by `company_number`."""
        for company in companies:
            write_json_record(
                self._base_dir / _COMPANY_SUBDIR,
                f"{company.company_number}.json",
                company.model_dump(mode="json"),
            )

    def write_addresses(self, addresses: Sequence[CanonicalAddress]) -> None:
        """Write one file per address, named by `company_number` and `address_type`."""
        for address in addresses:
            write_json_record(
                self._base_dir / _ADDRESS_SUBDIR,
                f"{address.company_number}_{address.address_type}.json",
                address.model_dump(mode="json"),
            )

    def write_search_matches(self, matches: Sequence[CanonicalSearchMatch]) -> None:
        """Write one file per search match, named by `query` and `company_number`."""
        for match in matches:
            write_json_record(
                self._base_dir / _SEARCH_MATCH_SUBDIR,
                f"{match.query}_{match.company_number}.json",
                match.model_dump(mode="json"),
            )
