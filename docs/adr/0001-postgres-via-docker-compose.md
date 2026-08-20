# ADR 0001: Postgres via Docker Compose, not SQLite

**Status:** Accepted

## Context

The data only needs to run locally — no external hosting is required. The simplest local
option would be a single SQLite file. The project is also meant to demonstrate the
backbone of a real data platform (bronze/silver/gold layering, schema migrations,
multiple future data sources), which is more naturally expressed with a real RDBMS.

## Decision

Use Postgres, run via `docker-compose`, as the only datastore. Schemas (`bronze`,
`silver`, `gold`) are used to express the medallion layering explicitly, rather than
table-name prefixes.

## Consequences

- Running the project requires Docker, not just a Python environment. This is accepted as
  the cost of "easy to install and use" — `docker compose up` is simpler for a reviewer
  than "install Postgres locally and configure it."
- Schema migrations (Alembic) are meaningful and testable, which they would not be for a
  single SQLite file recreated from scratch each run.
- Postgres schemas give bronze/silver/gold a real access-control and namespacing boundary,
  not just a naming convention.
