"""Pagination helper for Companies House's start_index search model.

Concrete to the raw /search/companies response shape because it's the
only paginated endpoint this codebase calls today. Generalize with a
TypeVar once a second paginated endpoint exists — doing so now would be
speculative. Operates on raw dicts, not validated schemas: schema
validation is a canonical-mapping-time concern, not a fetch/pagination
one (see docs/architecture.md section 5).
"""

from collections.abc import Callable, Iterator
from typing import Any


def paginate_by_start_index(
    fetch_page: Callable[[int], dict[str, Any]],
    items_per_page: int,
) -> Iterator[dict[str, Any]]:
    """Yield every item dict across all pages of a raw search response.

    Calls `fetch_page(start_index)` starting at 0 and advancing by the
    number of items actually returned each time (not `items_per_page`),
    since Companies House caps `items_per_page` server-side and may
    return a shorter page than requested — advancing by the requested
    size would silently skip records. Stops when a page returns no
    items or `total_results` has been reached (or is absent).
    """
    start_index = 0
    while True:
        page = fetch_page(start_index)
        items = page.get("items", [])
        if not items:
            return
        yield from items
        start_index += len(items)
        total_results = page.get("total_results")
        if total_results is not None and start_index >= total_results:
            return
