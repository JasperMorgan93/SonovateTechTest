"""Gold layer: reads silver back into a single analysis-ready DataFrame.

Deliberately simple for this first slice — a gold *table* per
`docs/architecture.md` would be a persisted, consumer-optimised data
product; here "gold" is the join, done once, in memory, so
`analytics/sono_test_answers.py` can query it with SQL instead of each
question re-deriving its own join over the silver files.

The join mirrors `docs/data-model.md`'s "Question -> data mapping":
`company_search_match` (scoped to one query) -> `company` -> registered
office `company_address`.
"""

from pathlib import Path

import pandas as pd

from company_data_platform.storage.silver.file_sink import SILVER_DIR
from company_data_platform.storage.silver.reader import read_addresses, read_companies, read_search_matches
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)

GOLD_DIR = Path(__file__).parent
_ADDRESS_COLUMNS = ["company_number", "premises"]


def _records_to_frame(records: list[dict], model: type) -> pd.DataFrame:
    """Build a DataFrame from silver records, falling back to the model's own
    column names when there are no records to infer columns from."""
    return pd.DataFrame(records) if records else pd.DataFrame(columns=list(model.model_fields))


def load_gold_companies(query: str, silver_dir: Path = SILVER_DIR) -> pd.DataFrame:
    """Build one row per company matched by `query`, with its status, type, dates, and premises.

    Left joins so a company missing an address still appears with `NaN` in
    the address columns rather than being silently dropped from the result.
    """
    search_matches = _records_to_frame(read_search_matches(silver_dir), CanonicalSearchMatch)
    search_matches = search_matches[search_matches["query"] == query]

    companies = _records_to_frame(read_companies(silver_dir), CanonicalCompany)
    addresses = _records_to_frame(read_addresses(silver_dir), CanonicalAddress)[_ADDRESS_COLUMNS]

    gold = search_matches.merge(companies, on="company_number", how="left", suffixes=("", "_company"))
    gold = gold.merge(addresses, on="company_number", how="left")
    return gold

def write_gold_companies(gold: pd.DataFrame, gold_dir: Path) -> None:
    """Write the gold DataFrame to one parquet file in ``gold_dir``."""
    gold_dir.mkdir(parents=True, exist_ok=True)
    gold.to_parquet(gold_dir / "companies.parquet", index=False)