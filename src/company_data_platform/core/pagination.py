"""Pagination helper for Companies House's start_index search model.

Concrete to SearchCompaniesResponse/SearchResultItem because
/search/companies is the only paginated endpoint this codebase calls
today. Generalize with a TypeVar once a second paginated endpoint
exists — doing so now would be speculative.
"""

from collections.abc import Callable, Iterator

from company_data_platform.ingestion.rest.companies_house.schemas import (
    SearchCompaniesResponse,
    SearchResultItem,
)


def paginate_by_start_index(
    fetch_page: Callable[[int], SearchCompaniesResponse],
    items_per_page: int,
) -> Iterator[SearchResultItem]:
    """Yield every `SearchResultItem` across all pages of a search response.

    Calls `fetch_page(start_index)` starting at 0 and incrementing by
    `items_per_page`, stopping when a page returns no items or
    `total_results` has been reached.
    """
    start_index = 0
    while True:
        page = fetch_page(start_index)
        if not page.items:
            return
        yield from page.items
        start_index += items_per_page
        if page.total_results is not None and start_index >= page.total_results:
            return
