"""Writes raw API responses to the bronze layer as JSON files.

Bronze preserves exactly what a source sent, alongside retrieval
metadata, so reprocessing after a bug fix or schema change never
requires re-hitting the API. This is a file-based bronze store — a
deliberate simplification of the Postgres-backed design in
docs/data-model.md for this first ingestion slice, not a database.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from company_data_platform.storage.json_file import write_json_record

BRONZE_DIR = Path(__file__).parent

SEARCH_RESULT_SUBDIR = "ch_search_result"


class BronzeWriter:
    """Base class for writing raw API responses to bronze as JSON files.

    Holds the state a real ingestion run will eventually need across
    many writes — today just the output directory, but this is the
    natural place for a shared run ID or high-watermark timestamp once
    ingestion needs to correlate or resume across multiple bronze
    writes in the same run. Source-specific subclasses (e.g.
    `CompaniesHouseBronzeWriter`) add the entity-shaped methods; this
    class only owns the shared "write this record as JSON" mechanics.
    """

    def __init__(self, base_dir: Path = BRONZE_DIR) -> None:
        self._base_dir = base_dir

    def write_record(self, subdir: str, filename: str, record: dict[str, Any]) -> Path:
        """Write one JSON record to `<base_dir>/<subdir>/<filename>`."""
        return write_json_record(self._base_dir / subdir, filename, record)


class CompaniesHouseBronzeWriter(BronzeWriter):
    """Writes Companies House API responses to bronze.
    
    When the imports expand to different sources, this subclass will own 
    the source-specific subdirectory names and the entity-shaped methods 
    (e.g. `write_search_result_page`).
    
    We should move this class into a sensible folder structure.
    """

    def write_search_result_page(
        self,
        query: str,
        start_index: int,
        payload: dict[str, Any],
        retrieved_at: datetime,
        source_url: str,
    ) -> Path:
        """Write one page of a /search/companies response to bronze.

        One JSON file per page, under `<base_dir>/ch_search_result/`, named
        with the query, start index, and retrieval timestamp so files sort
        chronologically and never collide across pages or runs. The file
        contains the raw payload plus enough metadata to answer "what did
        Companies House actually tell us, and when" without re-calling the
        API.
        """
        retrieved_at_slug = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
        filename = f"{query}_start{start_index}_{retrieved_at_slug}.json"

        record = {
            "query": query,
            "start_index": start_index,
            "source_url": source_url,
            "retrieved_at": retrieved_at.isoformat(),
            "payload": payload,
        }

        return self.write_record(SEARCH_RESULT_SUBDIR, filename, record)
