"""Reads canonical records back out of the file-based silver layer.

Mirrors `transform/companies_house/normalizer.py`'s bronze-reading pattern
(glob `*.json`, `json.loads` each file) — the read side of `FileSilverSink`,
used by the gold layer to load silver back into a DataFrame.
"""

import json
from pathlib import Path
from typing import Any

from company_data_platform.storage.silver.file_sink import (
    ADDRESS_SUBDIR,
    COMPANY_SUBDIR,
    SEARCH_MATCH_SUBDIR,
    SILVER_DIR,
)


def _read_json_records(directory: Path) -> list[dict[str, Any]]:
    """Read every JSON file directly under `directory`, in filename order."""
    if not directory.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]


def read_companies(silver_dir: Path = SILVER_DIR) -> list[dict[str, Any]]:
    """Read every `silver.company` record."""
    return _read_json_records(silver_dir / COMPANY_SUBDIR)


def read_addresses(silver_dir: Path = SILVER_DIR) -> list[dict[str, Any]]:
    """Read every `silver.company_address` record."""
    return _read_json_records(silver_dir / ADDRESS_SUBDIR)


def read_search_matches(silver_dir: Path = SILVER_DIR) -> list[dict[str, Any]]:
    """Read every `silver.company_search_match` record."""
    return _read_json_records(silver_dir / SEARCH_MATCH_SUBDIR)
