# ADR 0003: Ingestion organised by method, not by source

**Status:** Accepted

## Context

The obvious first structure for ingestion is one folder per source
(`sources/companies_house/...`). That works fine while there's one source and one way of
fetching it. But Companies House itself exposes three distinct ingestion mechanisms —
REST, bulk snapshot, streaming (guide 28) — with genuinely different concerns (pagination
vs. file download vs. long-lived-connection checkpointing). A per-source folder would
either mix all three transports into one module, or silently assume REST is the only
mechanism anything will ever need.

## Decision

Organise `ingestion/` by *method* first, *source* second:

```
ingestion/
├── base.py            # IngestionMethod ABC
├── rest/
│   ├── base.py           # RestIngestionMethod(IngestionMethod)
│   └── companies_house/  # a REST source
├── bulk/               # reserved: BulkIngestionMethod
└── streaming/           # reserved: StreamingIngestionMethod
```

`IngestionMethod` defines the contract (take parameters, fetch, persist to bronze, return
a summary) without assuming a transport. `RestIngestionMethod` adds what every REST source
needs (HTTP session, rate limiter, retry, paginator); a bulk or streaming base class would
add its own shared concerns instead. A concrete source (Companies House today) subclasses
the method base that matches how it's actually being ingested.

## Consequences

- Adding Companies House's bulk data product later is "add `BulkIngestionMethod` +
  `ingestion/bulk/companies_house/`", not a rewrite of existing REST code.
- A second REST-based source reuses `RestIngestionMethod` (and therefore `core/`)
  directly — no duplicated rate limiting/retry/pagination code.
- One extra layer of abstraction (`IngestionMethod` → `RestIngestionMethod` → concrete
  source) exists before there is a second method or a second source to justify it. This is
  accepted because the split is cheap, the guide independently documents three transports
  for this exact API, and it's a common structural mistake to bake "REST" into the base
  case and have to retrofit it later.
