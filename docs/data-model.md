# Data model

Three Postgres schemas: `bronze`, `silver`, `gold` (reserved, empty — see
[architecture.md](architecture.md) and [ADR 0002](adr/0002-bronze-silver-gold-layering.md)).

## bronze

Raw, unmodified API responses. Nothing here is ever mutated after insert — reprocessing
means re-reading bronze, not re-calling the API.

### `bronze.ch_search_result`

One row per page of a `/search/companies` call.

| column           | type      | notes                                   |
|-------------------|-----------|------------------------------------------|
| id                 | bigserial | PK                                        |
| query              | text      | the `q` parameter, e.g. `sono`            |
| start_index        | int       | pagination offset used for this page      |
| items_per_page     | int       |                                            |
| total_results      | int       | as reported by the API on this page       |
| source_url         | text      | full request URL                          |
| retrieved_at       | timestamptz |                                          |
| payload            | jsonb     | full raw response body                    |

### `bronze.ch_company_profile`

One row per `/company/{company_number}` call.

| column           | type      | notes                                   |
|-------------------|-----------|--------------------------------------------|
| id                 | bigserial | PK                                          |
| company_number     | text      |                                              |
| source_url         | text      |                                              |
| source_etag        | text      | nullable — not every response carries one   |
| retrieved_at       | timestamptz |                                            |
| payload            | jsonb     | full raw response body                      |

## silver

The platform's **canonical schema** — the platform's own model of a company, not
Companies House's field names typed 1:1. Populated by
`transform/companies_house/normalizer.py`, which maps `bronze.ch_company_profile`
payloads onto the canonical models in `transform/canonical/company.py`
(`CanonicalCompany`, `CanonicalAddress`, `CanonicalPreviousName`, `CanonicalSicCode`)
before upserting. Upserted on `company_number` (and child natural keys) — re-running
normalisation is idempotent. A second source describing companies would target the same
canonical models and the same silver tables, tagged via `source_system` for lineage.

### `silver.company`

| column               | type    | notes                                                      |
|-----------------------|---------|--------------------------------------------------------------|
| company_number         | text    | PK                                                             |
| title                  | text    |                                                                |
| company_status         | text    | raw enum value, e.g. `active`, `dissolved` (guide 24)        |
| company_status_detail  | text    | nullable                                                       |
| company_type           | text    | raw enum value, e.g. `ltd`, `limited-partnership`              |
| company_subtype        | text    | nullable                                                       |
| jurisdiction           | text    | nullable                                                       |
| date_of_creation       | date    | nullable                                                       |
| date_of_cessation      | date    | nullable — present only for dissolved-type companies           |
| source_system          | text    | `companies_house` — lineage column for future multi-source use |
| source_retrieved_at    | timestamptz | copied from the bronze row this was derived from            |

### `silver.company_previous_name`

| column        | type      | notes                     |
|----------------|-----------|-----------------------------|
| id              | bigserial | PK                           |
| company_number  | text      | FK → `silver.company`       |
| name            | text      |                              |
| effective_from  | date      | nullable                    |
| ceased_on       | date      | nullable                    |

### `silver.company_sic`

| column        | type      | notes                 |
|----------------|-----------|-------------------------|
| id              | bigserial | PK                       |
| company_number  | text      | FK → `silver.company`   |
| sic_code        | text      | raw code, stored as-is  |

### `silver.company_address`

Covers registered office today; `address_type` allows other address kinds (e.g. service
address) to be added without a schema change.

| column         | type      | notes                                                  |
|-----------------|-----------|-----------------------------------------------------------|
| id               | bigserial | PK                                                           |
| company_number   | text      | FK → `silver.company`                                      |
| address_type     | text      | `registered_office` for everything ingested by this task    |
| premises         | text      | raw string, e.g. `6-8`, `14B`, `1st Floor 45 Main St` — kept as-is, not parsed here |
| address_line_1   | text      | nullable                                                     |
| address_line_2   | text      | nullable                                                     |
| locality         | text      | nullable                                                     |
| region           | text      | nullable                                                     |
| postal_code      | text      | nullable                                                     |
| country          | text      | nullable                                                     |

### `silver.company_search_match`

Links a search query to the companies it returned, so "the set of companies from Q1" is
an explicit, queryable set rather than an assumption baked into later queries — and so a
second, differently-scoped search doesn't collide with this one.

| column        | type        | notes                          |
|----------------|-------------|-----------------------------------|
| id              | bigserial   | PK                                  |
| query           | text        | e.g. `sono`                         |
| company_number  | text        | FK → `silver.company`               |
| retrieved_at    | timestamptz |                                      |

## gold

No persisted gold tables — still reserved per ADR 0002. For this first slice, "gold" is
`storage/gold/loader.py`'s `load_gold_companies()`: it reads silver back in and performs,
once, in memory, the same join the question-mapping table below describes
(`company_search_match` scoped to one query -> `company` -> registered-office
`company_address`), returning a single pandas DataFrame. `analytics/sono_test_answers.py`
runs SQL (via DuckDB) against that DataFrame to answer the six questions, and
`scripts/analyse_sono_search.py` is the runnable entry point (same pattern as
`ingest_sono_search.py` / `normalise_sono_search.py`).

## Question → data mapping

| # | Question                                              | Source                                                                                   |
|---|--------------------------------------------------------|--------------------------------------------------------------------------------------------|
| 1 | Companies matching `sono`                               | `count(distinct company_number)` in `company_search_match` where `query = 'sono'`         |
| 2 | Of those, how many active                                | join `company_search_match` → `company`, filter `company_status = 'active'`               |
| 3 | Avg dissolved lifespan (creation → cessation), in days   | join as above, filter `date_of_cessation is not null`, `avg(date_of_cessation - date_of_creation)` |
| 4 | First `limited-partnership` created                      | join as above, filter `company_type = 'limited-partnership'`, `min(date_of_creation)`     |
| 5 | Companies with `vate` in title                            | join as above, filter `title ilike '%vate%'`                                              |
| 6 | Sum of premises digits per company type                   | join `company_search_match` → `company` → `company_address` (registered_office), extract digits from `premises` in Python, group by `company_type` |

Q6 is deliberately **not** a persisted column: extracting digits from an arbitrary
premises string (`6-8` → `68`, `14B` → `14`, `1st Floor 45 Main St` → `145`) is a
one-off parsing rule for this specific question, not a general property of an address. It
lives as a pure function in `analytics/sono_test_answers.py`, tested directly against the
examples given in the test spec, rather than as a schema concern.
