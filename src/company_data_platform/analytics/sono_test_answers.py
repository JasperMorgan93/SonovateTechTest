"""Answers to the Sonovate tech test's six questions, run as SQL against the gold layer.

See `docs/BDD/data_engineer_test_spec.txt` for the questions and
`docs/data-model.md`'s "Question -> data mapping" for how each maps onto
`storage/gold/loader.py`'s joined DataFrame (`company_search_match` scoped
to one query, joined to `company` and registered-office `company_address`).

Q6 (sum of premises digits per company type) is the one exception: turning
`"6-8"` into `68` is a one-off parsing rule for this question, not a
general property of an address, so it stays a plain, independently testable
Python function rather than a SQL expression.
"""

import re
from dataclasses import dataclass

import duckdb
import pandas as pd

_DIGIT_PATTERN = re.compile(r"\d")


def extract_premises_digits(premises: str | None) -> int:
    """Concatenate every digit in `premises` into a single number.

    Per the test spec: `"6-8"` -> `68`, `"14B"` -> `14`,
    `"1st Floor 45 Main St"` -> `145`. Returns `0` for a premises with no
    digits at all (including `None`/`NaN`).
    """
    if not premises or (isinstance(premises, float) and pd.isna(premises)):
        return 0
    digits = "".join(_DIGIT_PATTERN.findall(premises))
    return int(digits) if digits else 0


@dataclass(frozen=True)
class SonoAnswers:
    """The six test-spec answers for one search query."""

    total_matches: int
    active_count: int
    avg_dissolved_lifespan_days: float | None
    first_limited_partnership_created: str | None
    vate_titles: list[str]
    premises_digit_sum_by_type: dict[str, int]


def compute_sono_answers(gold: pd.DataFrame) -> SonoAnswers:
    """Answer all six questions against `gold` (one row per matched company)."""
    total_matches = duckdb.sql("SELECT COUNT(DISTINCT company_number) FROM gold").fetchone()[0]

    active_count = duckdb.sql("SELECT COUNT(*) FROM gold WHERE company_status = 'active'").fetchone()[0]

    avg_lifespan_days = duckdb.sql(
        """
        SELECT AVG(CAST(date_of_cessation AS DATE) - CAST(date_of_creation AS DATE))
        FROM gold
        WHERE date_of_cessation IS NOT NULL AND date_of_creation IS NOT NULL
        """
    ).fetchone()[0]

    first_lp_created = duckdb.sql(
        "SELECT MIN(CAST(date_of_creation AS DATE)) FROM gold WHERE company_type = 'limited-partnership'"
    ).fetchone()[0]

    vate_titles = [
        row[0] for row in duckdb.sql("SELECT title FROM gold WHERE title ILIKE '%vate%' ORDER BY title").fetchall()
    ]

    premises_by_type = duckdb.sql("SELECT company_type, premises FROM gold").fetchdf()
    premises_by_type["premises_digits"] = premises_by_type["premises"].apply(extract_premises_digits)
    digit_sums = premises_by_type.groupby("company_type")["premises_digits"].sum()

    return SonoAnswers(
        total_matches=total_matches,
        active_count=active_count,
        avg_dissolved_lifespan_days=float(avg_lifespan_days) if avg_lifespan_days is not None else None,
        first_limited_partnership_created=str(first_lp_created) if first_lp_created is not None else None,
        vate_titles=vate_titles,
        premises_digit_sum_by_type=digit_sums.to_dict(),
    )
