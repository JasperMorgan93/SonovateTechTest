"""Pagination helpers for Companies House's start_index search model.

Concrete to the raw /search/companies response shape because it's the
only paginated endpoint this codebase calls today. Generalize with a
TypeVar once a second paginated endpoint exists — doing so now would be
speculative. Operates on raw dicts, not validated schemas: schema
validation is a canonical-mapping-time concern, not a fetch/pagination
one (see docs/architecture.md section 5).
"""

from collections.abc import Callable, Iterator
from typing import Any

MAX_START_INDEX = 1000
"""Companies House returns errors once start_index goes beyond roughly
the first 1000 results (see docs/BDD/data_engineer_test_spec.txt) — this
caps pagination defensively so a large result set fails closed (stops
cleanly) rather than crashing against the live API."""


def paginate_pages_by_start_index(
    fetch_page: Callable[[int], dict[str, Any]],
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (start_index, page) for each raw page of a search response.

    Calls `fetch_page(start_index)` starting at 0 and advancing by the
    number of items actually returned each time (not a fixed page
    size), since Companies House caps items-per-page server-side and
    may return a shorter page than requested — advancing by the
    requested size would silently skip records. Stops when a page
    returns no items, `total_results` has been reached (or is absent),
    or `start_index` would reach `MAX_START_INDEX`.
    """
    start_index = 0
    while start_index < MAX_START_INDEX:
        page = fetch_page(start_index)
        items = page.get("items", [])
        if not items:
            return
        yield start_index, page
        start_index += len(items)
        total_results = page.get("total_results")
        if total_results is not None and start_index >= total_results:
            return


def paginate_by_start_index(fetch_page: Callable[[int], dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Yield every item dict across all pages of a raw search response.

    A thin flattening wrapper over `paginate_pages_by_start_index` — see
    that function for the pagination/stop-condition semantics.
    """
    for _start_index, page in paginate_pages_by_start_index(fetch_page):
        yield from page.get("items", [])
