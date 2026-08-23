"""The silver-layer write contract, decoupled from any storage technology.

`Normalizer` subclasses depend only on this interface, not on a concrete
storage choice. The current implementation (`FileSilverSink`) writes JSON
files, matching the file-based bronze store for this first slice — but
because `Normalizer` only ever talks to a `SilverSink`, a future sink that
writes to a DataFrame, or to Postgres, is a new implementation of this
interface, not a change to the normalisation logic.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)


class SilverSink(ABC):
    """Where canonical records go once they're mapped and cleaned."""

    @abstractmethod
    def write_companies(self, companies: Sequence[CanonicalCompany]) -> None:
        """Persist canonical companies to the silver layer."""

    @abstractmethod
    def write_addresses(self, addresses: Sequence[CanonicalAddress]) -> None:
        """Persist canonical addresses to the silver layer."""

    @abstractmethod
    def write_search_matches(self, matches: Sequence[CanonicalSearchMatch]) -> None:
        """Persist canonical search matches to the silver layer."""
