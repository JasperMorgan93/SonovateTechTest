from datetime import date, datetime, timezone

import pandas as pd

from company_data_platform.storage.gold.loader import load_gold_companies
from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.canonical.company import (
    CanonicalAddress,
    CanonicalCompany,
    CanonicalSearchMatch,
)


def _seed_silver(tmp_path):
    sink = FileSilverSink(base_dir=tmp_path)
    sink.write_companies(
        [
            CanonicalCompany(
                company_number="1",
                title="SONO ONE LTD",
                company_type="ltd",
                company_status="active",
                date_of_creation=date(2020, 1, 1),
                source_system="companies_house",
                source_retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
            ),
            CanonicalCompany(
                company_number="2",
                title="OTHER LTD",
                company_type="ltd",
                company_status="active",
                source_system="companies_house",
                source_retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
            ),
        ]
    )
    sink.write_addresses([CanonicalAddress(company_number="1", address_type="registered_office", premises="6-8")])
    sink.write_search_matches(
        [
            CanonicalSearchMatch(query="sono", company_number="1", retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc)),
            CanonicalSearchMatch(query="other", company_number="2", retrieved_at=datetime(2026, 8, 23, tzinfo=timezone.utc)),
        ]
    )
    return tmp_path


def test_load_gold_companies_scopes_to_the_given_query(tmp_path):
    silver_dir = _seed_silver(tmp_path)

    gold = load_gold_companies("sono", silver_dir=silver_dir)

    assert list(gold["company_number"]) == ["1"]
    assert gold.iloc[0]["title"] == "SONO ONE LTD"
    assert gold.iloc[0]["premises"] == "6-8"


def test_load_gold_companies_left_joins_company_without_an_address(tmp_path):
    silver_dir = _seed_silver(tmp_path)

    gold = load_gold_companies("other", silver_dir=silver_dir)

    assert list(gold["company_number"]) == ["2"]
    assert pd.isna(gold.iloc[0]["premises"])


def test_load_gold_companies_returns_empty_frame_for_unmatched_query(tmp_path):
    silver_dir = _seed_silver(tmp_path)

    gold = load_gold_companies("nonexistent", silver_dir=silver_dir)

    assert gold.empty
