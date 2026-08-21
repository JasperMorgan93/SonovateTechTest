# Companies House Data Platform Architecture

## Purpose

This document defines the proposed data architecture for the Companies House data engineering project.

The goal is to build a production-quality data platform around Companies House data rather than treating the Companies House API as the application itself.

The architecture separates:

1. **Bronze** — raw source data
2. **Silver** — trusted, normalised canonical data
3. **Gold** — consumer-optimised data products

This separation provides data lineage, reprocessing capability, a stable internal data model, and flexibility in how the resulting data is consumed.

---

## High-Level Architecture

```text
                         COMPANIES HOUSE
                  ┌──────────┬──────────┐
                  │          │          │
                REST       BULK      STREAMING
                  │          │          │
                  └──────────┼──────────┘
                             ↓
                    ┌─────────────────┐
                    │     BRONZE      │
                    │                 │
                    │ Raw source data │
                    │ Source metadata │
                    │ Ingestion info  │
                    └────────┬────────┘
                             ↓
                 Canonical Mapping
                 + Validation
                 + Cleansing
                             ↓
                    ┌─────────────────┐
                    │     SILVER      │
                    │                 │
                    │ Local SQL DB    │
                    │ Normalised      │
                    │ Canonical model │
                    │ Trusted data    │
                    └────────┬────────┘
                             ↓
                 Transformation /
                 Enrichment /
                 Aggregation
                             ↓
                    ┌─────────────────┐
                    │      GOLD       │
                    │                 │
                    │ Data products   │
                    │ Query models    │
                    │ Aggregations    │
                    │ Search models   │
                    └────────┬────────┘
                             ↓
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
             API          Dashboard       Analysis
```

---

# 1. Bronze Layer — Source Truth

The Bronze layer should remain deliberately close to the Companies House source.

Its primary responsibility is to preserve what Companies House actually provided, rather than immediately forcing the source into our own relational model.

### Bronze should contain

Where appropriate, each ingested record should retain:

- Raw JSON payload
- Source endpoint/resource
- Company number or relevant source identifier
- Retrieval timestamp
- Source update timestamp where available
- ETag where available
- Payload hash
- API/resource version
- Ingestion/run ID
- Relevant ingestion metadata

### Why retain raw data?

This gives the platform a source-level audit trail:

> What did Companies House actually tell us at the time?

It also means that downstream transformations can be changed and replayed without necessarily making another request to Companies House.

This is particularly important when dealing with schema evolution. If Companies House introduces a new JSON member, we retain the original source payload even if our current canonical model does not yet use that field.

### Bronze principles

- Preserve source fidelity.
- Avoid unnecessary transformation.
- Make ingestion traceable.
- Support replay/reprocessing.
- Keep sufficient metadata to understand provenance.
- Treat the source payload as the authoritative representation of what was received.

Bronze is therefore **not intended to be the primary application-facing data store**.

---

# 2. Canonical Schema

Between Bronze and Silver sits a conceptual canonical mapping layer.

The purpose is to prevent our internal data model from becoming tightly coupled to the Companies House API structure.

```text
Companies House JSON
        ↓
Canonical Schema
        ↓
Our Relational Data Model
```

The canonical schema represents the business meaning of the incoming data in a stable internal form.

For example, Companies House may expose nested structures containing:

- Company information
- Registered office address
- SIC codes
- Previous names
- Officers
- Officer appointments
- Persons with significant control
- Filings
- Charges
- Accounts information

The canonical layer allows these concepts to be mapped consistently into our own model.

### Why this separation matters

The Companies House API is an external contract.

Our internal data model is an application/platform contract.

They should not be the same thing.

This gives us the ability to:

- Handle Companies House schema changes.
- Validate incoming data before persistence.
- Apply cleansing and standardisation.
- Maintain consistent internal naming and types.
- Support additional sources in the future.
- Change application models without rewriting ingestion.
- Reprocess historical Bronze data through newer transformations.

---

# 3. Silver Layer — Trusted Stored Data

The Silver layer is the platform's trusted, queryable representation of Companies House data.

For this project, the Silver layer should be implemented using a **local SQL database**.

The data should be normalised and stored according to our canonical data model rather than simply mirroring Companies House JSON.

### Example model

A simplified model might contain:

```text
company
├── company_id
├── company_number
├── name
├── status
├── company_type
├── jurisdiction
├── incorporation_date
├── cessation_date
└── ...

company_address
├── company_id
├── address_type
├── premises
├── address_line_1
├── locality
├── region
├── postal_code
└── country

company_sic
├── company_id
└── sic_code

company_previous_name
├── company_id
├── previous_name
├── effective_from
└── effective_to

officer
...

officer_appointment
...

company_psc
...

company_filing
...

company_charge
...
```

The exact schema should be developed incrementally as the MVP requirements become clearer.

### Silver principles

- Normalised relational structure.
- Strong data types.
- Referential integrity.
- Consistent identifiers.
- Validated and cleansed data.
- Clear relationships between entities.
- Queryable independently of the source API.
- Traceability back to Bronze.

Silver should represent **trusted data**, not necessarily the most convenient representation for every consumer.

---

# 4. Gold Layer — Consumer-Optimised Data Products

Gold should sit above the trusted Silver model and provide data that is optimised for consumption.

It should not be defined solely as an "aggregation layer".

A better definition is:

> **Gold contains consumer-optimised data products, including aggregations, denormalised views and purpose-built query models.**

Some Gold datasets will be aggregates.

Others may simply reshape Silver data to make a particular consumption pattern efficient.

### Example Gold datasets

```text
gold_company_summary
gold_company_financial_status
gold_company_ownership
gold_company_officer_network
gold_company_filings
gold_company_search
gold_company_industry_summary
```

For example, a consumer may want:

```text
company_number
company_name
status
industry
registered_address
active_officer_count
active_psc_count
latest_accounts
latest_filing
charge_count
```

They should not need to understand the underlying Silver relationships.

### Gold principles

- Optimised for known consumption patterns.
- Can be denormalised where useful.
- Can contain aggregations.
- Can contain calculated or derived fields.
- Should remain traceable to Silver.
- Should not dictate the presentation technology.
- Should be designed as reusable data products.

---

# 5. Consumption Layer

A key architectural principle is that Gold should **not be coupled to a single presentation tool**.

The same Gold data products should be capable of supporting different consumers.

```text
                         GOLD
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
          REST API      Dashboard     Analytics
             │             │             │
             ↓             ↓             ↓
          App/UI       Power BI      SQL/Notebooks
```

Potential consumers include:

- A FastAPI service
- A web or mobile application
- Business intelligence dashboards
- Direct SQL analysis
- Data science notebooks
- Future analytical or AI services

This means the data platform remains independent from the presentation layer.

If the presentation technology changes, the underlying Bronze/Silver/Gold architecture does not need to change.

---

# 6. End-to-End Data Flow

The complete architecture can therefore be represented as:

```text
┌──────────────────────────────────────────────────────────────┐
│                    COMPANIES HOUSE                           │
│                                                              │
│       REST API          Bulk Data          Streaming API     │
└───────────┬────────────────┬──────────────────┬──────────────┘
            │                │                  │
            └────────────────┼──────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                         BRONZE                               │
│                                                              │
│ Raw payloads • Source metadata • ETags • Hashes • Run IDs    │
│                                                              │
│ Purpose: preserve source truth + enable reprocessing         │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                 Canonical Schema Layer
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                         SILVER                               │
│                                                              │
│                    Local SQL Database                        │
│                                                              │
│ Normalised • Validated • Relational • Trusted • Queryable    │
│                                                              │
│ Purpose: establish our canonical Companies House model       │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                 Transformation / Enrichment
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                          GOLD                                │
│                                                              │
│     Consumer-oriented datasets / views / aggregations        │
│                                                              │
│ Purpose: make trusted data easy and efficient to consume     │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          FastAPI        BI / Dashboards   SQL / Analysis
             ↓
          Frontend
```

---

# 7. Architectural Benefits

This architecture gives the project several important properties.

### Source abstraction

The application does not need to know how Companies House represents its data.

### Reprocessing

Historical Bronze data can be processed again if the canonical model or transformation logic changes.

### Data lineage

A Gold value can ultimately be traced back through Silver and the original Bronze payload.

### Schema resilience

Changes to the Companies House API can be absorbed by the ingestion/canonicalisation process without automatically propagating through the entire platform.

### Multiple consumers

Different applications and analytical tools can consume the same trusted data products.

### Separation of concerns

Each layer has a clear responsibility:

| Layer | Responsibility |
|---|---|
| Bronze | Preserve source data |
| Canonical | Translate source concepts into our internal representation |
| Silver | Store trusted, normalised data |
| Gold | Produce consumer-optimised data products |
| Consumption | Present/use the data |

---

# 8. MVP Direction

The project should avoid attempting to model the entire Companies House universe immediately.

A sensible starting point is to build a vertical slice through all layers.

For example:

```text
Company Profile
      ↓
Bronze raw response
      ↓
Canonical company schema
      ↓
Silver company + address + SIC
      ↓
Gold company summary
      ↓
FastAPI endpoint
```

Once this works reliably, additional entities can be introduced:

- Officers
- PSCs
- Filings
- Charges
- Accounts
- Previous names
- Other relevant Companies House resources

This allows the architecture to be proven before the data model becomes unnecessarily large.

---

# Architectural Principle

The central principle for this project is:

> **Companies House is the source; Bronze preserves it, the canonical layer interprets it, Silver establishes our trusted data model, and Gold turns that trusted data into reusable products for multiple consumers.**

The objective is therefore not simply to build a Companies House API client.

It is to demonstrate a **small but production-minded data platform** that can ingest, preserve, standardise, store, transform and expose external data in a way that remains maintainable as the scope grows.
