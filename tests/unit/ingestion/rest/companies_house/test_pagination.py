from company_data_platform.ingestion.rest.companies_house.pagination import paginate_by_start_index
from company_data_platform.ingestion.rest.companies_house.schemas import (
    SearchCompaniesResponse,
    SearchResultItem,
)


def test_paginate_by_start_index_yields_items_across_multiple_pages():
    pages = {
        0: SearchCompaniesResponse(
            items=[SearchResultItem(company_number="1"), SearchResultItem(company_number="2")],
            total_results=3,
        ),
        2: SearchCompaniesResponse(items=[SearchResultItem(company_number="3")], total_results=3),
    }

    results = list(paginate_by_start_index(lambda start_index: pages[start_index], items_per_page=2))

    assert [item.company_number for item in results] == ["1", "2", "3"]


def test_paginate_by_start_index_stops_on_empty_page():
    pages = {
        0: SearchCompaniesResponse(items=[SearchResultItem(company_number="1")], total_results=None),
        1: SearchCompaniesResponse(items=[], total_results=None),
    }

    results = list(paginate_by_start_index(lambda start_index: pages[start_index], items_per_page=1))

    assert [item.company_number for item in results] == ["1"]


def test_paginate_by_start_index_advances_by_actual_page_size_not_requested_size():
    pages = {
        0: SearchCompaniesResponse(
            items=[SearchResultItem(company_number="1"), SearchResultItem(company_number="2")],
            total_results=4,
        ),
        2: SearchCompaniesResponse(
            items=[SearchResultItem(company_number="3"), SearchResultItem(company_number="4")],
            total_results=4,
        ),
    }

    # Caller asks for pages of 5, but the server only ever returns 2 at a time.
    results = list(paginate_by_start_index(lambda start_index: pages[start_index], items_per_page=5))

    assert [item.company_number for item in results] == ["1", "2", "3", "4"]
