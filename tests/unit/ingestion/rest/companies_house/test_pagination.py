from company_data_platform.ingestion.rest.companies_house.pagination import (
    MAX_START_INDEX,
    paginate_by_start_index,
    paginate_pages_by_start_index,
)


def test_paginate_by_start_index_yields_items_across_multiple_pages():
    pages = {
        0: {"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 3},
        2: {"items": [{"company_number": "3"}], "total_results": 3},
    }

    results = list(paginate_by_start_index(lambda start_index: pages[start_index]))

    assert [item["company_number"] for item in results] == ["1", "2", "3"]


def test_paginate_by_start_index_stops_on_empty_page():
    pages = {
        0: {"items": [{"company_number": "1"}], "total_results": None},
        1: {"items": [], "total_results": None},
    }

    results = list(paginate_by_start_index(lambda start_index: pages[start_index]))

    assert [item["company_number"] for item in results] == ["1"]


def test_paginate_by_start_index_advances_by_actual_page_size_not_requested_size():
    pages = {
        0: {"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 4},
        2: {"items": [{"company_number": "3"}, {"company_number": "4"}], "total_results": 4},
    }

    # Caller asks for pages of 5, but the server only ever returns 2 at a time.
    results = list(paginate_by_start_index(lambda start_index: pages[start_index]))

    assert [item["company_number"] for item in results] == ["1", "2", "3", "4"]


def test_paginate_by_start_index_stops_when_page_omits_total_results_key():
    pages = {
        0: {"items": [{"company_number": "1"}]},
        1: {"items": []},
    }

    results = list(paginate_by_start_index(lambda start_index: pages[start_index]))

    assert [item["company_number"] for item in results] == ["1"]


def test_paginate_pages_by_start_index_yields_raw_pages_not_flattened_items():
    pages = {
        0: {"items": [{"company_number": "1"}, {"company_number": "2"}], "total_results": 3},
        2: {"items": [{"company_number": "3"}], "total_results": 3},
    }

    results = list(paginate_pages_by_start_index(lambda start_index: pages[start_index]))

    assert results == [(0, pages[0]), (2, pages[2])]


def test_paginate_pages_by_start_index_stops_at_max_start_index_ceiling():
    def fetch_page(start_index: int) -> dict:
        # A query with far more matches than the ceiling allows reaching —
        # every page returns exactly one item, so start_index increments by 1.
        return {"items": [{"company_number": str(start_index)}], "total_results": 5000}

    results = list(paginate_pages_by_start_index(fetch_page))

    assert len(results) == MAX_START_INDEX
    assert results[0][0] == 0
    assert results[-1][0] == MAX_START_INDEX - 1
