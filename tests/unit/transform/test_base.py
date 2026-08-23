from datetime import datetime, timezone

import pytest

from company_data_platform.storage.silver.file_sink import FileSilverSink
from company_data_platform.transform.base import Normalizer, RunSummary
from company_data_platform.transform.canonical.company import CanonicalCompany, CanonicalSearchMatch

_COMPANY = CanonicalCompany(
    company_number="17013908",
    title="CENSOR AI LIMITED",
    company_type="ltd",
    source_system="companies_house",
    source_retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
)
_MATCH = CanonicalSearchMatch(
    query="sono",
    company_number="17013908",
    retrieved_at=datetime(2026, 8, 23, 11, 9, 50, tzinfo=timezone.utc),
)


class _RecordingNormalizer(Normalizer):
    """A minimal Normalizer that logs which steps `run()` invoked, in order."""

    def __init__(self, silver_sink):
        super().__init__(silver_sink)
        self.calls: list[str] = []

    def read_bronze(self):
        self.calls.append("read_bronze")
        return ["one-bronze-record"]

    def map_to_canonical(self, records):
        self.calls.append("map_to_canonical")
        return [_COMPANY], [], [_MATCH]

    def deduplicate(self, companies, addresses, matches):
        self.calls.append("deduplicate")
        return super().deduplicate(companies, addresses, matches)

    def clean(self, companies, addresses, matches):
        self.calls.append("clean")
        return super().clean(companies, addresses, matches)

    def upsert_silver(self, companies, addresses, matches):
        self.calls.append("upsert_silver")
        return super().upsert_silver(companies, addresses, matches)


def test_normalizer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Normalizer(silver_sink=None)


def test_run_invokes_pipeline_steps_in_order(tmp_path):
    normalizer = _RecordingNormalizer(silver_sink=FileSilverSink(base_dir=tmp_path))

    normalizer.run()

    assert normalizer.calls == ["read_bronze", "map_to_canonical", "deduplicate", "clean", "upsert_silver"]


def test_default_deduplicate_returns_inputs_unchanged(tmp_path):
    normalizer = _RecordingNormalizer(silver_sink=FileSilverSink(base_dir=tmp_path))

    companies, addresses, matches = normalizer.deduplicate([_COMPANY], [], [_MATCH])

    assert companies == [_COMPANY]
    assert addresses == []
    assert matches == [_MATCH]


def test_default_clean_returns_inputs_unchanged(tmp_path):
    normalizer = _RecordingNormalizer(silver_sink=FileSilverSink(base_dir=tmp_path))

    companies, addresses, matches = normalizer.clean([_COMPANY], [], [_MATCH])

    assert companies == [_COMPANY]
    assert addresses == []
    assert matches == [_MATCH]


def test_run_returns_summary_with_counts_written(tmp_path):
    normalizer = _RecordingNormalizer(silver_sink=FileSilverSink(base_dir=tmp_path))

    summary = normalizer.run()

    assert summary == RunSummary(companies=1, addresses=0, search_matches=1)


def test_run_writes_records_via_the_injected_silver_sink(tmp_path):
    normalizer = _RecordingNormalizer(silver_sink=FileSilverSink(base_dir=tmp_path))

    normalizer.run()

    assert (tmp_path / "company" / "17013908.json").exists()
    assert (tmp_path / "company_search_match" / "sono_17013908.json").exists()
