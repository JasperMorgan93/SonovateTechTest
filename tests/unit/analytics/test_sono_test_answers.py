import pandas as pd
import pytest

from company_data_platform.analytics.sono_test_answers import compute_sono_answers, extract_premises_digits


@pytest.mark.parametrize(
    ("premises", "expected"),
    [
        ("6-8", 68),
        ("14B", 14),
        ("1st Floor 45 Main St", 145),
        (None, 0),
        ("No digits here", 0),
    ],
)
def test_extract_premises_digits(premises, expected):
    assert extract_premises_digits(premises) == expected


def _gold_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "company_number": "1",
                "title": "SONO ONE LTD",
                "company_type": "ltd",
                "company_status": "active",
                "date_of_creation": None,
                "date_of_cessation": None,
                "premises": "6-8",
            },
            {
                "company_number": "2",
                "title": "SONOVATE LTD",
                "company_type": "limited-partnership",
                "company_status": "dissolved",
                "date_of_creation": pd.Timestamp("2020-01-01"),
                "date_of_cessation": pd.Timestamp("2020-01-11"),
                "premises": "14B",
            },
        ]
    )


def test_compute_sono_answers_against_a_small_gold_frame():
    answers = compute_sono_answers(_gold_frame())

    assert answers.total_matches == 2
    assert answers.active_count == 1
    assert answers.avg_dissolved_lifespan_days == 10.0
    assert answers.first_limited_partnership_created == "2020-01-01"
    assert answers.vate_titles == ["SONOVATE LTD"]
    assert answers.premises_digit_sum_by_type == {"ltd": 68, "limited-partnership": 14}


def test_compute_sono_answers_handles_no_dissolved_companies():
    gold = pd.DataFrame(
        [
            {
                "company_number": "1",
                "title": "SONO ONE LTD",
                "company_type": "ltd",
                "company_status": "active",
                "date_of_creation": None,
                "date_of_cessation": None,
                "premises": None,
            }
        ]
    )

    answers = compute_sono_answers(gold)

    assert answers.avg_dissolved_lifespan_days is None
    assert answers.first_limited_partnership_created is None
    assert answers.vate_titles == []
    assert answers.premises_digit_sum_by_type == {"ltd": 0}
