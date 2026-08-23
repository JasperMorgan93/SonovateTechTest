from datetime import date, datetime, timezone

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)
from scripts.analyse_sono_search import analyse_sono_search


def test_analyse_sono_search_answers_all_six_questions_from_silver(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    sink.write_companies(
        [
            CanonicalCompany(
                company_number="1",
                title="SONOVATE LTD",
                company_type="ltd",
                company_status="dissolved",
                date_of_creation=date(2020, 1, 1),
                date_of_cessation=date(2020, 1, 11),
                source_system="companies_house",
                source_retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
            )
        ]
    )
    sink.write_addresses([CanonicalAddress(company_number="1", address_type="registered_office", premises="6-8")])
    sink.write_search_matches(
        [CanonicalSearchMatch(query="sono", company_number="1", retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc))]
    )

    gold_dir = tmp_path / "gold"
    answers = analyse_sono_search("sono", silver_dir=tmp_path, gold_dir=gold_dir)

    assert (gold_dir / "companies.parquet").exists()
    assert answers.total_matches == 1
    assert answers.active_count == 0
    assert answers.avg_dissolved_lifespan_days == 10.0
    assert answers.vate_titles == ["SONOVATE LTD"]
    assert answers.premises_digit_sum_by_type == {"ltd": 68}
