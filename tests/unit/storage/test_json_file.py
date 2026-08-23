import json

from company_data_platform.storage.json_file import write_json_record


def test_write_json_record_creates_file_with_record_contents(tmp_path):
    output_path = write_json_record(tmp_path / "some_subdir", "some_file.json", {"key": "value"})

    assert output_path == tmp_path / "some_subdir" / "some_file.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"key": "value"}


def test_write_json_record_creates_missing_parent_directories(tmp_path):
    output_path = write_json_record(tmp_path / "nested" / "subdir", "record.json", {"a": 1})

    assert output_path.exists()
