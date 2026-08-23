"""Read the 'sono' search silver data into a gold DataFrame and answer the six test questions.

Run with: python scripts/analyse_sono_search.py

Assumes `scripts/ingest_sono_search.py` and `scripts/normalise_sono_search.py`
have already populated bronze and silver. Reads silver back into a single
gold DataFrame (`storage/gold/loader.py`) and answers the six questions from
`docs/BDD/data_engineer_test_spec.txt` by running SQL against it
(`analytics/sono_test_answers.py`).
"""

from pathlib import Path

from company_data_platform.analytics.sono_test_answers import SonoAnswers, compute_sono_answers
from company_data_platform.storage.gold.loader import GOLD_DIR, SILVER_DIR, load_gold_companies, write_gold_companies

QUERY = "sono"


def analyse_sono_search(query: str, silver_dir: Path = SILVER_DIR, gold_dir: Path = GOLD_DIR) -> SonoAnswers:
    """Load `query`'s gold DataFrame and answer all six test-spec questions."""
    gold = load_gold_companies(query, silver_dir=silver_dir)
    write_gold_companies(gold, gold_dir)
    return compute_sono_answers(gold)


def print_answers(query: str, answers: SonoAnswers) -> None:
    """Print the six answers in the same terminal-report style as the other scripts."""
    print(" SONO SEARCH ANALYSIS COMPLETE ")
    print("---")
    print(f"Q1. Companies matching '{query}': {answers.total_matches}")
    print(f"Q2. Of those, active: {answers.active_count}")
    print(f"Q3. Avg dissolved lifespan (days): {answers.avg_dissolved_lifespan_days}")
    print(f"Q4. First limited-partnership created: {answers.first_limited_partnership_created}")
    print(f"Q5. Companies with 'vate' in title ({len(answers.vate_titles)}): {answers.vate_titles}")
    print("Q6. Sum of premises digits by company type:")
    for company_type, digit_sum in sorted(answers.premises_digit_sum_by_type.items()):
        print(f"    {company_type}: {digit_sum}")


def main() -> None:
    """Load the gold DataFrame for `QUERY` and print all six test-spec answers."""
    answers = analyse_sono_search(QUERY)
    print_answers(QUERY, answers)


if __name__ == "__main__":
    main()
