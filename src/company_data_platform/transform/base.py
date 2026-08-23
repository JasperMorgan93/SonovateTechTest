"""The normalisation-phase contract: bronze -> canonical -> silver.

`Normalizer` fixes the pipeline shape (`run()`) while leaving each step
overridable. `read_bronze` and `map_to_canonical` are source-specific and
must be implemented by a subclass (e.g. `CompaniesHouseNormalizer`).
`deduplicate` and `clean` default to identity — no cleansing rule is baked
in here — but give any subclass, or a future revision of one, a fixed seam
to add that logic without touching `run()` itself. `upsert_silver` writes
through an injected `SilverSink`, so persistence (files today, a DataFrame
or a database later) is a storage-layer concern, not a normalizer one.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel

from company_data_platform.storage.silver.base import SilverSink
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)

CanonicalBatch = tuple[list[CanonicalCompany], list[CanonicalAddress], list[CanonicalSearchMatch]]


class RunSummary(BaseModel):
    """How many canonical records of each kind a normalisation run wrote."""

    companies: int
    addresses: int
    search_matches: int


class Normalizer(ABC):
    """Base class for mapping one source's bronze records to the silver layer."""

    def __init__(self, silver_sink: SilverSink) -> None:
        self._silver_sink = silver_sink

    def run(self) -> RunSummary:
        """Read bronze, map to canonical, clean/deduplicate, then persist to silver."""
        records = self.read_bronze()
        companies, addresses, matches = self.map_to_canonical(records)
        companies, addresses, matches = self.deduplicate(companies, addresses, matches)
        companies, addresses, matches = self.clean(companies, addresses, matches)
        return self.upsert_silver(companies, addresses, matches)

    @abstractmethod
    def read_bronze(self) -> Sequence[Any]:
        """Read this source's raw bronze records."""

    @abstractmethod
    def map_to_canonical(self, records: Sequence[Any]) -> CanonicalBatch:
        """Map raw bronze records to canonical companies, addresses, and search matches."""

    def deduplicate(
        self,
        companies: list[CanonicalCompany],
        addresses: list[CanonicalAddress],
        matches: list[CanonicalSearchMatch],
    ) -> CanonicalBatch:
        """Remove duplicate canonical records. Identity by default; override to add a rule."""
        return companies, addresses, matches

    def clean(
        self,
        companies: list[CanonicalCompany],
        addresses: list[CanonicalAddress],
        matches: list[CanonicalSearchMatch],
    ) -> CanonicalBatch:
        """Apply cleansing rules to canonical records. Identity by default; override to add a rule."""
        return companies, addresses, matches

    def upsert_silver(
        self,
        companies: list[CanonicalCompany],
        addresses: list[CanonicalAddress],
        matches: list[CanonicalSearchMatch],
    ) -> RunSummary:
        """Persist canonical records via the injected `SilverSink`."""
        self._silver_sink.write_companies(companies)
        self._silver_sink.write_addresses(addresses)
        self._silver_sink.write_search_matches(matches)
        return RunSummary(companies=len(companies), addresses=len(addresses), search_matches=len(matches))
