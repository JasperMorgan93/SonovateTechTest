# ADR 0002: Bronze/silver/gold layering; gold deferred

**Status:** Accepted

## Context

The test asks six specific questions about a fixed, small set of companies. The stated
goal beyond the test itself is a foundation for a normalised data platform that can grow
to more sources and more processing. Building a full curated/aggregated ("gold") layer
and a consumption surface for six fixed questions would be scope the task didn't ask for.

## Decision

Adopt a three-schema medallion layout in Postgres:

- **bronze** — raw API responses (JSONB) plus retrieval metadata. Populated by ingestion,
  never mutated.
- **silver** — typed, normalised relational tables. Populated by a transform step reading
  only from bronze.
- **gold** — reserved schema, no tables yet. This is the natural home for curated
  marts/aggregates once there's a real consumer that needs them.

The six test-question answers are computed by a Python `analytics` module that queries
**silver directly** — not a persisted gold table. This is a conscious "gold-lite": correct
today, and trivially upgraded to real materialised gold tables later without touching
bronze or silver.

## Consequences

- Adding a gold layer later means adding a materialisation step that reads from silver and
  writes to `gold.*`, plus repointing consumers — not restructuring bronze or silver.
- The six answers are recomputed on every run rather than cached in a table. Acceptable at
  this data volume; would need revisiting if this became a high-frequency or high-volume
  query path.
- No conflict-resolution logic exists yet for a second source writing into the same
  `silver.company` rows. Deferred until there is a second source to design against —
  designing it speculatively now risks getting it wrong.
