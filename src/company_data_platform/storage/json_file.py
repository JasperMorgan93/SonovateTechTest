"""Shared mechanics for writing a record to disk as an indented JSON file.

Used by both the bronze writer (raw API payloads) and the file-based silver
sink (canonical records) — the "write this dict as JSON under this
directory" step is identical for both; only what gets written and where
differs.
"""

import json
from pathlib import Path
from typing import Any


def write_json_record(directory: Path, filename: str, record: dict[str, Any]) -> Path:
    """Write `record` as indented JSON to `<directory>/<filename>`, creating `directory` if needed."""
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / filename
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return output_path
