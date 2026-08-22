import os

import pytest


@pytest.fixture(autouse=True)
def _clear_companies_house_env(monkeypatch):
    """Ensure CompaniesHouseConfig tests never read a developer's real
    environment — every COMPANIES_HOUSE_* var is cleared before each test."""
    for key in list(os.environ):
        if key.startswith("COMPANIES_HOUSE_"):
            monkeypatch.delenv(key, raising=False)
