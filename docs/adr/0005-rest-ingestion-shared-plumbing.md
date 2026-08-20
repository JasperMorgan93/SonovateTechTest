# ADR 0005: Shared rate limiting, retry and pagination for REST ingestion

**Status:** Accepted

## Context

The API guide is explicit and repeated on this point: a central rate limiter (not one per
worker), a central retry policy (not ad-hoc retries per call site), and a single
pagination implementation (not reimplemented per endpoint) are what separate a reliable
integration from a script that happens to work today (guide 5, 7, 33, 42). This
matters more than usual here because rate-limit and retry bugs are the kind that pass
locally and fail under load or on a second source.

## Decision

`RestIngestionMethod` owns one instance each of: HTTP session, token-bucket rate limiter,
retry policy (`tenacity`, exponential backoff + jitter, retrying `429`/transient
`5xx`/network errors only), and generic `start_index` paginator — all constructed from the
injected config (ADR 0004). `CompaniesHouseIngestor` calls through this shared machinery
for every request; it does not open its own session or implement its own backoff.

Errors are normalised into a `CompaniesHouseError` hierarchy
(`AuthenticationError`, `ValidationError`, `NotFoundError`, `RateLimitError`,
`ServerError`) at the client boundary, so calling code branches on error type, not raw
HTTP status codes.

## Consequences

- Every REST source built on `RestIngestionMethod` gets correct rate-limiting and retry
  behaviour by construction, not by remembering to copy it.
- `400/401/404/422/406` are treated as non-retryable by default (guide 33) — a source
  that has a genuine reason to retry a specific 4xx must say so explicitly, rather than it
  happening by accident.
- The alphabetical/dissolved-search pagination variant (`search_above`/`search_below`) is
  not covered by the generic paginator and is out of scope for this task; a source that
  needs it would add a second paginator strategy rather than forcing every pagination
  style through one shape.
