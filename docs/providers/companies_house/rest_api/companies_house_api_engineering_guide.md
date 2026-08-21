# Companies House API — Engineering Guide

**Prepared:** 20 August 2026  
**Scope:** Companies House Public Data API, with adjacent guidance on the Document API, Streaming API and bulk data products where they materially affect architecture.

## 1. Executive summary

Companies House provides a REST API for retrieving public company-register data. The Public Data API is read-only and exposes company profiles, searches, officers, filing history, charges, insolvency, registers, UK establishments, exemptions, Persons with Significant Control (PSC) data and related resources.

The most important engineering constraints are:

1. **Authentication:** Public Data API requests use an API key sent via HTTP Basic Authentication, with the API key as the username and an empty password.
2. **Rate limit:** The default limit is **600 requests per five minutes per application**. Exceeding it produces HTTP `429`; repeatedly exceeding or attempting to bypass limits can result in a ban.
3. **Data shape is not immutable:** Clients must tolerate JSON member ordering changing and must tolerate previously unseen fields.
4. **Pagination is common:** Many list/search endpoints use `items_per_page` and `start_index`; do not assume a single response contains the complete dataset.
5. **ETags are exposed:** Many resources return an `ETag`; retain it as part of a robust caching/change-detection strategy.
6. **Company numbers are the key identifier:** Once a company number is known, prefer direct resource endpoints over repeatedly searching by name.
7. **Do not use the REST API for bulk extraction if a bulk product or streaming feed is more appropriate.** The REST rate limit makes naïve full-register crawling unsuitable.
8. **Use the links returned by Companies House:** company profiles provide links to related resources such as officers, filing history, charges, insolvency and PSC.
9. **Expect optional/deprecated fields:** Some resources contain legacy fields marked deprecated. Build around the current fields and treat deprecated fields as migration liabilities.
10. **API versioning exists at resource level:** Companies House versions resources using MIME types/content negotiation. Breaking changes increment a resource version; non-breaking additions such as new fields do not.

For a production integration, the recommended architecture is a small internal Companies House client/service with centralised authentication, throttling, retries, pagination, response validation, caching, observability and schema-tolerant persistence.

---

## 2. Official documentation map

### Primary documentation

- [Companies House developer portal](https://developer.companieshouse.gov.uk/)
- [Companies House Public Data API reference](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference)
- [Companies House API getting started](https://developer-specs.company-information.service.gov.uk/guides/gettingStarted)
- [Authorisation](https://developer-specs.company-information.service.gov.uk/guides/authorisation)
- [Developer guidelines](https://developer-specs.company-information.service.gov.uk/guides/developerGuidelines)
- [Rate limiting](https://developer-specs.company-information.service.gov.uk/guides/rateLimiting)
- [API versioning](https://developer-specs.company-information.service.gov.uk/guides/versioning)
- [Introduction / REST API](https://developer-specs.company-information.service.gov.uk/guides/introduction)

### Adjacent services worth knowing about

- [Developer API suite](https://developer-specs.company-information.service.gov.uk/)
- [Document API](https://developer-specs.company-information.service.gov.uk/document-api/reference)
- [Streaming API](https://developer-specs.company-information.service.gov.uk/streaming-api/guides/overview)
- [Streaming API authentication](https://developer-specs.company-information.service.gov.uk/streaming-api/guides/authentication)
- [Companies House data products / bulk data](https://www.gov.uk/guidance/companies-house-data-products)

---

# 3. Public Data API overview

The Public Data API is a read-only REST API exposing public company information.

Base URL:

`https://api.company-information.service.gov.uk`

Requests are standard HTTP `GET` requests for public resources.

The API currently exposes:

| Area | Endpoint |
|---|---|
| Registered office | `GET /company/{company_number}/registered-office-address` |
| Company profile | `GET /company/{company_number}` |
| Advanced company search | `GET /advanced-search/companies` |
| Search all | `GET /search` |
| Search companies | `GET /search/companies` |
| Search officers | `GET /search/officers` |
| Search disqualified officers | `GET /search/disqualified-officers` |
| Alphabetical company search | `GET /alphabetical-search/companies` |
| Dissolved company search | `GET /dissolved-search/companies` |
| Company officers | `GET /company/{company_number}/officers` |
| Officer appointment | `GET /company/{company_number}/appointments/{appointment_id}` |
| Company registers | `GET /company/{company_number}/registers` |
| Charges | `GET /company/{company_number}/charges` |
| Individual charge | `GET /company/{company_number}/charges/{charge_id}` |
| Filing history | `GET /company/{company_number}/filing-history` |
| Individual filing | `GET /company/{company_number}/filing-history/{transaction_id}` |
| Insolvency | `GET /company/{company_number}/insolvency` |
| Exemptions | `GET /company/{company_number}/exemptions` |
| Corporate officer disqualifications | `GET /disqualified-officers/corporate/{officer_id}` |
| Natural officer disqualifications | `GET /disqualified-officers/natural/{officer_id}` |
| Officer appointments | `GET /officers/{officer_id}/appointments` |
| UK establishments | `GET /company/{company_number}/uk-establishments` |
| PSC list | `GET /company/{company_number}/persons-with-significant-control` |
| PSC statements | `GET /company/{company_number}/persons-with-significant-control-statements` |
| PSC notifications | `GET /persons-with-significant-control/{psc_id}/notifications` |
| Individual PSC | `GET /company/{company_number}/persons-with-significant-control/individual/{notification_id}` |
| Corporate PSC | `GET /company/{company_number}/persons-with-significant-control/corporate-entity/{notification_id}` |
| Legal-person PSC | `GET /company/{company_number}/persons-with-significant-control/legal-person/{notification_id}` |
| PSC beneficial-owner variants | Multiple dedicated endpoints |
| Super-secure PSC variants | Multiple dedicated endpoints |

The official reference should be treated as the authoritative endpoint catalogue because Companies House can add resources and fields.

---

# 4. Authentication

## 4.1 API key authentication

The Public Data API requires an API key.

The API key is transmitted using HTTP Basic Authentication:

- username = API key
- password = empty

Example:

```bash
curl -u "$COMPANIES_HOUSE_API_KEY:" \
  "https://api.company-information.service.gov.uk/company/00000006"
```

The API key is not a bearer token.

## 4.2 Key management

Companies House specifically recommends:

- Do not embed keys in source code.
- Do not commit keys to the source tree.
- Store keys in environment variables, a secret manager or equivalent configuration.
- Restrict API-key use by IP address/domain where appropriate.
- Regenerate keys regularly, and particularly with application releases.
- Delete obsolete keys.

### Recommended implementation

For an Azure-based production system:

`Application -> Secret store -> Companies House client -> API`

Do not pass the key through frontend/mobile code.

If the integration is used by a public web/mobile application, the API call should normally go through your backend rather than exposing the Companies House key to clients.

---

# 5. Rate limiting

## 5.1 Official limit

The default rate limit is:

**600 requests per five-minute period per application.**

That is an average ceiling of roughly:

- 120 requests/minute
- 2 requests/second

However, do **not** design the application around constantly consuming the full allowance.

If the limit is exceeded, Companies House returns:

`429 Too Many Requests`

The rate limit resets at the end of the five-minute period.

Companies House explicitly reserves the right to ban applications that regularly exceed or attempt to bypass the rate limit.

## 5.2 Production design

Use a central rate limiter rather than letting every worker independently make calls.

For example:

```text
                ┌──────────────┐
Frontend/API -> │ Internal CH  │
Workers ------>│ Client       │
Jobs ---------->│              │
                └──────┬───────┘
                       │
                 Rate limiter
                       │
                 Retry policy
                       │
               Companies House
```

This matters particularly if multiple application instances share the same API key.

### Recommended controls

- Global token-bucket/leaky-bucket limiter.
- Maximum concurrency.
- Request timeout.
- Retry only retryable failures.
- Exponential backoff with jitter.
- Explicit handling of `429`.
- Metrics for requests, status codes and rate-limit events.
- Queue bulk work rather than firing requests concurrently without coordination.

### Important

Do not create multiple API keys simply to circumvent the rate limit.

The documentation explicitly warns against attempts to bypass limits.

---

# 6. Error handling

The API uses standard HTTP status codes.

Common cases include:

| Status | Meaning | Typical action |
|---|---|---|
| `200` | Successful response | Process response |
| `400` | Bad request | Fix request; normally do not retry |
| `401` | Unauthorised | Check API key/configuration |
| `404` | Resource not found | Treat as legitimate absence where appropriate |
| `406` | Invalid/unacceptable API version/content negotiation | Review `Accept` header |
| `410` | Requested API resource version expired | Upgrade resource version |
| `422` | Validation/parameter issue on some endpoints | Fix request |
| `429` | Rate limited | Back off and retry |
| `5xx` | Server-side failure | Retry with backoff where appropriate |

The exact status codes available differ by endpoint, so endpoint-specific documentation should remain the final authority.

## Error response shape

The API defines an error resource containing an `errors` array. Errors can include:

- `error`
- `error_values`
- `location`
- `location_type`
- `type`

The `type` can include:

- `ch:service`
- `ch:validation`

Validation errors can identify whether the problematic input was a query parameter or JSON path.

### Recommended error model

Normalise external errors internally:

```text
CompaniesHouseError
├── AuthenticationError
├── ValidationError
├── NotFoundError
├── RateLimitError
├── VersionError
├── ServerError
└── UnknownApiError
```

Do not treat every `4xx` as a transient failure.

---

# 7. Pagination

Pagination is one of the most important implementation details.

Common endpoints expose:

- `items_per_page`
- `start_index`
- `total_results` or `total_count`

For example:

```http
GET /company/00000006/officers?items_per_page=100&start_index=0
```

then:

```http
GET /company/00000006/officers?items_per_page=100&start_index=100
```

until the complete result set has been retrieved.

## Recommended paginator

Implement pagination once in your API client.

Conceptually:

```python
start_index = 0

while True:
    response = get(
        endpoint,
        params={
            "items_per_page": page_size,
            "start_index": start_index,
        },
    )

    items = response["items"]
    yield from items

    if start_index + len(items) >= response["total_results"]:
        break

    start_index += len(items)
```

Do not duplicate this logic separately for officers, filings, charges, PSCs, etc.

## Important caveat

Some search APIs use different pagination mechanics.

Alphabetical and dissolved-company searches expose `search_above` / `search_below` keys, while best-match searches can use `start_index`.

Therefore, pagination should be implemented per endpoint family rather than assuming every endpoint behaves identically.

---

# 8. Search endpoints

## 8.1 Search companies

`GET /search/companies`

Required:

- `q`

Optional:

- `items_per_page`
- `start_index`
- `restrictions`

Example:

```http
GET /search/companies?q=tesco
```

This is appropriate for interactive company-name lookup.

### Important architectural recommendation

Use company search to **resolve a name to a company number**.

Once you have:

`company_number`

prefer direct company resources.

For example:

```text
User searches "Acme"
        ↓
/search/companies?q=Acme
        ↓
Company number: 12345678
        ↓
/company/12345678
```

This avoids repeatedly performing expensive fuzzy searches.

---

## 8.2 Advanced company search

`GET /advanced-search/companies`

Filters include:

- `company_name_includes`
- `company_name_excludes`
- `company_status`
- `company_subtype`
- `company_type`
- `dissolved_from`
- `dissolved_to`
- `incorporated_from`
- `incorporated_to`
- `location`
- `sic_codes`
- `size`
- `start_index`

The `size` parameter supports a range of 1–5000 according to the current documentation.

This endpoint is particularly useful for building datasets based on criteria such as:

> Active UK companies in SIC code X incorporated after date Y.

### Do not confuse this with a bulk ingestion API

Even though `size` can be large, this is still a search endpoint subject to API rate limits.

For large-scale extraction, use an appropriate bulk product or streaming architecture.

---

## 8.3 Search all

`GET /search`

Searches across multiple types of Companies House data.

Possible result kinds include:

- companies
- officers
- PSCs
- disqualified officers

The response includes a `kind` field identifying the type of result.

This can be useful for a broad user-facing search box but is less appropriate when your application already knows what entity type it is looking for.

---

## 8.4 Officer search

`GET /search/officers`

Required:

- `q`

Optional:

- `items_per_page`
- `start_index`

Useful for finding an officer before traversing their appointments.

---

## 8.5 Alphabetical company search

`GET /alphabetical-search/companies`

Parameters include:

- `q`
- `search_above`
- `search_below`
- `size`

The documented maximum `size` is 100.

This uses ordered paging rather than the ordinary `start_index` model.

---

## 8.6 Dissolved company search

`GET /dissolved-search/companies`

Parameters include:

- `q`
- `search_type`
- `search_above`
- `search_below`
- `size`
- `start_index`

`search_type` supports:

- `alphabetical`
- `best-match`
- `previous-name-dissolved`

The documented maximum `size` is 100.

---

# 9. Company profile

The most important endpoint is:

`GET /company/{company_number}`

Example:

```http
GET /company/00000006
```

The company profile can contain:

- company name
- company number
- status
- status detail
- creation date
- cessation date
- company type
- subtype
- jurisdiction
- registered office
- service address where applicable
- SIC codes
- previous names
- accounts information
- confirmation statement information
- filing links
- officer links
- charges links
- insolvency links
- PSC links
- registers links
- UK establishment links
- annotations
- other specialist information

## Key recommendation

Treat the profile as a **root resource**.

After retrieving it, follow its resource links when you need deeper information.

For example:

```text
Company Profile
├── officers
├── filing history
├── charges
├── insolvency
├── exemptions
├── registers
├── PSC
├── PSC statements
└── UK establishments
```

This creates a natural resource graph.

---

# 10. Registered office

`GET /company/{company_number}/registered-office-address`

Returns the current registered office address.

Do not assume all address fields exist.

Address fields can include:

- premises
- address line 1
- address line 2
- locality
- region
- postal code
- country

Some fields are optional.

---

# 11. Officers

## List officers

`GET /company/{company_number}/officers`

Parameters include:

- `items_per_page`
- `start_index`
- `register_view`
- `register_type`
- `order_by`

`register_type` can include:

- `directors`
- `secretaries`
- `llp_members`

`order_by` can include:

- `appointed_on`
- `resigned_on`
- `surname`

## Officer data

Officer records can contain:

- name
- appointment dates
- resignation date
- role
- service/correspondence address
- date of birth month/year
- nationality
- country of residence
- identification information
- corporate officer information
- identity verification information where applicable
- a `person_number` in applicable data

### Watch out

A person's date of birth is not necessarily a full date. The API commonly exposes month/year rather than day.

Do not create a database model that assumes a complete DOB.

---

# 12. Officer appointments

`GET /officers/{officer_id}/appointments`

Parameters include:

- `filter=active`
- `items_per_page`
- `start_index`

This allows you to traverse:

```text
Officer
  ↓
Appointments
  ↓
Companies
```

This is useful when answering questions such as:

> Which companies is this officer associated with?

It is not necessarily the best mechanism for building a complete officer database; bulk products may be more suitable for large-scale use.

---

# 13. Charges

Company charges are available through:

`GET /company/{company_number}/charges`

and individual charges through:

`GET /company/{company_number}/charges/{charge_id}`

Charges can include information about mortgages/security interests and their status.

Important fields include charge number, dates, classifications and release/cessation information.

Charges are paginated when using the list endpoint.

---

# 14. Filing history

Company filing history:

`GET /company/{company_number}/filing-history`

Individual filing:

`GET /company/{company_number}/filing-history/{transaction_id}`

The list supports:

- `category`
- `items_per_page`
- `start_index`

Filing categories include:

- accounts
- address
- annual-return
- capital
- change-of-name
- incorporation
- liquidation
- miscellaneous
- mortgage
- officers
- resolution

A filing history item can contain:

- transaction ID
- filing date
- category
- type
- subcategory
- description
- annotations
- associated filings
- resolutions
- document metadata link
- page count
- paper-filed indicator

## Document API relationship

Filing history may expose a `links.document_metadata` URL.

That points into the separate Document API.

This means:

```text
Public Data API
      ↓
Filing history
      ↓
Document metadata
      ↓
Document content
```

Do not assume that the Public Data API itself contains the complete filing document.

---

# 15. Document API

The separate Document API provides:

- document metadata
- document content

Endpoints include:

`GET /document/{document_id}`

and:

`GET /document/{document_id}/content`

Available content types can include:

- PDF
- JSON
- XML
- XHTML
- ZIP
- CSV

Not every document necessarily has every format.

This service should be treated as a separate dependency from the Public Data API.

---

# 16. Persons with Significant Control (PSC)

PSC information is spread across multiple resources.

Core list:

`GET /company/{company_number}/persons-with-significant-control`

PSC statements:

`GET /company/{company_number}/persons-with-significant-control-statements`

There are also dedicated endpoints for:

- individual PSCs
- corporate entities
- legal persons
- beneficial-owner variants
- super-secure PSC variants
- PSC statements
- PSC notifications

## Pagination

The main PSC lists use:

- `items_per_page`
- `start_index`
- `register_view`

`register_view=true` changes the result to register-specific information and can restrict results to currently relevant/active records according to the resource.

### Important data-quality point

PSC data is not simply a list of "current owners".

It includes states, cessation dates, statements and notifications.

If your business logic asks:

> Who currently controls this company?

you should explicitly model active/ceased status and the relevant PSC semantics rather than just selecting every PSC record.

---

# 17. Registers

`GET /company/{company_number}/registers`

The registers resource can provide information such as registered company officers.

It also exposes an `ETag`.

The register view is distinct from the ordinary officer endpoint, so don't assume:

```text
/officers
```

and:

```text
/registers
```

are interchangeable.

---

# 18. Insolvency

`GET /company/{company_number}/insolvency`

Returns company insolvency information.

The company profile also provides a link to the insolvency resource.

Use the profile's link rather than constructing URLs throughout application code where practical.

---

# 19. Exemptions

`GET /company/{company_number}/exemptions`

This provides exemption information associated with a company.

Treat this as optional company metadata rather than assuming it exists for every company.

---

# 20. Officer disqualifications

Two endpoints exist:

```text
GET /disqualified-officers/corporate/{officer_id}
GET /disqualified-officers/natural/{officer_id}
```

The distinction matters because corporate and natural officers have different resource models.

---

# 21. UK establishments

`GET /company/{company_number}/uk-establishments`

This is relevant to foreign companies and UK establishment records.

Do not assume every company has a UK establishment resource containing data.

---

# 22. ETags and caching

Many Public Data API resources expose an `ETag`.

Examples include company profiles, officer lists, registers, PSC resources and other list resources.

ETags are useful for:

- change detection
- cache validation
- avoiding unnecessary downstream processing
- storing resource versions
- building incremental synchronisation

## Recommended model

Store:

```text
resource_url
etag
retrieved_at
payload_hash
payload
```

Even if you initially only need the data, storing the ETag makes future incremental strategies easier.

### Important

Do not assume every endpoint has identical caching behaviour. Treat the endpoint's documented headers as authoritative.

---

# 23. JSON schema resilience

This is one of the most important official developer guidelines.

Companies House says applications must:

- tolerate JSON member ordering changing
- expect members that the application has not seen before

Therefore:

### Bad

```python
if response.keys() == EXPECTED_KEYS:
    ...
```

### Better

```python
company_name = response.get("company_name")
company_number = response.get("company_number")
```

And for persistence:

- tolerate new fields
- avoid failing an entire ingestion because an extra property appeared
- distinguish required fields from optional fields
- maintain explicit schema-version/migration handling internally

## Recommended storage strategy

For a data platform, consider keeping both:

1. **Raw response**
2. **Normalised relational representation**

For example:

```text
raw_companies_house.company_profile
        ↓
normalisation pipeline
        ↓
company
company_address
company_sic
company_name_history
company_accounts_status
...
```

This protects you against future schema changes and makes reprocessing possible.

---

# 24. Enumerations

Companies House uses enumeration values extensively.

Examples include:

- company status
- company type
- filing categories
- officer roles
- PSC statement types
- jurisdiction
- address country

The documentation points to Companies House enumeration mappings.

### Do not hard-code descriptions everywhere

Prefer:

```text
company_status = "active"
```

and map it to:

```text
Active
```

in your application.

Store the raw enumeration value.

This is especially important because new values can appear.

---

# 25. Deprecated fields

The API contains fields that are explicitly marked deprecated.

Examples in company profiles include older account/annual-return fields and legacy boolean indicators such as:

- `has_been_liquidated`
- `has_charges`
- `has_insolvency_history`
- `is_community_interest_company`

The documentation indicates newer links/subtypes should be used instead.

### Engineering rule

If a field is marked deprecated:

- do not build new business logic around it
- keep compatibility handling if needed
- document the replacement
- create a migration path
- monitor API changes

---

# 26. API versioning

Companies House versions resources independently using MIME types and HTTP content negotiation.

There is **no single global API version**.

A resource version can be requested with the `Accept` header.

The response identifies the version using `Content-Type`.

## Breaking vs non-breaking

A version increment is expected for breaking changes such as:

- removing a field
- renaming a field
- changing a field type
- changing nested structure

Adding fields is considered non-breaking and does not necessarily increment the version.

## Default behaviour

If no `Accept` header is provided, or it is set to:

```text
application/json
```

or:

```text
*/*
```

the latest version is returned.

## Deprecation

When a resource version is deprecated, Companies House can provide a:

`CH-Expiry-Date`

response header.

Expired versions can eventually return:

`410 Gone`

An invalid version can return:

`406 Not Acceptable`

### Recommended approach

Unless you have a strong compatibility reason to pin a version:

- use the documented current version
- monitor API-change announcements
- make schemas additive/tolerant
- test against real API responses
- avoid relying on undocumented fields

---

# 27. Data freshness

Companies House describes the API data as live and real-time.

This does **not** mean:

> every company resource changes instantly after an event occurs elsewhere.

It means the API exposes live register data as maintained by Companies House.

Your application should therefore record:

```text
source_updated_at
retrieved_at
```

where possible.

Do not confuse:

- date the company filed something
- date Companies House processed it
- date the underlying event occurred
- date your system retrieved it

These can differ.

---

# 28. Bulk data vs REST API

This is critical if the intended project will ingest large numbers of companies.

Companies House offers free bulk data products in addition to the REST API.

The company data product is a monthly snapshot containing basic information for live companies, including:

- company type
- registered office
- SIC
- company status
- accounts/confirmation-statement dates
- previous company names

The company snapshot is split across downloadable ZIP/CSV files.

Companies House also provides other bulk products, including accounts and PSC data, and additional bulk products exist for other datasets.

## Recommended principle

Use:

### REST API

For:

- interactive lookups
- individual companies
- small batches
- on-demand enrichment
- user-facing search
- targeted refreshes

### Bulk products

For:

- initial large-scale ingestion
- rebuilding a local warehouse
- creating a company master table
- historical/broad datasets
- reducing API traffic

### Streaming API

For:

- near-real-time updates
- maintaining a local copy after initial ingestion
- event-driven processing
- high-volume change capture

---

# 29. Streaming API

The Streaming API is a separate product.

It is especially relevant if the objective becomes:

> Keep my database synchronised with Companies House.

The streaming service provides real-time changes and uses a long-running HTTP connection.

The documentation warns that repeatedly connecting and disconnecting is expensive and may result in rate limiting.

## Connection limit

A maximum of **two concurrent connections per account** can be made to the Streaming API.

Opening another connection above this limit can cause the oldest connection to be closed.

## Reconnection

Clients should implement backoff.

Documented guidance includes:

- `429`: wait one minute before reconnecting
- retryable HTTP error: retry after approximately 10 seconds
- network error: back off for a few seconds

## Timepoints

Streaming events have timepoints.

Persist the last successfully processed timepoint.

On reconnect, use the stored timepoint so the consumer can resume without losing continuity.

This is extremely important for reliable ingestion.

---

# 30. Recommended large-scale architecture

If the long-term goal is a local Companies House dataset, I would not build:

```text
Your system
   ↓
600 REST calls / 5 minutes
   ↓
Entire Companies House register
```

Instead:

```text
                    ┌──────────────────────┐
                    │ Companies House      │
                    │ monthly bulk data    │
                    └──────────┬───────────┘
                               │
                         Initial load
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Raw data lake        │
                    │ ADLS / object store  │
                    └──────────┬───────────┘
                               │
                         Transform
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Company warehouse    │
                    │ / operational DB     │
                    └──────────┬───────────┘
                               ▲
                               │
                         Incremental events
                               │
                    ┌──────────┴───────────┐
                    │ Streaming API        │
                    └──────────────────────┘

                  REST API
                     │
              targeted enrichment
                     │
                     ▼
               Internal API
```

This architecture keeps REST usage for cases where it is genuinely useful.

---

# 31. If building a company enrichment service

A practical internal API might expose:

```text
GET /companies/{company_number}
GET /companies/{company_number}/officers
GET /companies/{company_number}/psc
GET /companies/{company_number}/filings
GET /companies/{company_number}/charges
GET /companies/{company_number}/insolvency

GET /companies/search?q=...
GET /officers/search?q=...
```

Internally:

```text
Client
  ↓
Your API
  ↓
Company service
  ├── cache
  ├── database
  ├── Companies House API client
  └── rate limiter
```

This means the rest of your application never needs to know:

- the Companies House API key
- pagination rules
- rate limits
- retry behaviour
- response versioning
- external schema quirks

---

# 32. Caching strategy

Caching is particularly useful for company profiles.

A simple strategy:

```text
Request company
       ↓
Local cache?
   ├── fresh → return
   │
   └── stale/missing
          ↓
    Companies House
          ↓
       update cache
          ↓
        return
```

For data that changes infrequently, use a sensible TTL.

For data that matters operationally, use explicit refresh policies.

Do not rely solely on a generic TTL for critical data.

Store:

- `retrieved_at`
- `source_etag`
- `source_url`
- raw response
- normalised fields

---

# 33. Retry strategy

Recommended:

### Retry

- `429`
- transient `5xx`
- transient network failures

### Usually don't retry

- `400`
- `401`
- `404`
- `422`
- `406`

unless the application has a specific reason to correct and retry.

Use exponential backoff with jitter:

```text
attempt 1 → short delay
attempt 2 → longer delay
attempt 3 → longer delay
...
```

For `429`, respect the API's rate-limiting behaviour rather than immediately retrying.

---

# 34. Observability

At minimum, record:

```text
companies_house.request.count
companies_house.request.duration
companies_house.response.2xx
companies_house.response.4xx
companies_house.response.5xx
companies_house.rate_limited
companies_house.retry.count
companies_house.pagination.pages
companies_house.cache.hit
companies_house.cache.miss
```

Also log:

- endpoint
- status code
- latency
- request correlation ID
- company number where applicable
- retry count

Never log the API key.

---

# 35. Data modelling recommendations

For a relational database, avoid putting everything into one giant company table.

A reasonable starting model:

```text
company
company_previous_name
company_sic
company_address
company_account_status
company_confirmation_statement
company_officer
officer_appointment
company_charge
company_filing
company_psc
company_psc_statement
company_insolvency
company_uk_establishment
```

Use stable identifiers where provided.

For external source records, also retain:

```text
source
source_url
source_etag
source_retrieved_at
raw_payload
```

This makes source reconciliation much easier.

---

# 36. Data-quality watch-outs

## Company names

Do not treat company name as a stable identifier.

Names can change.

Use:

`company_number`

as the primary company identity.

## Company status

Do not assume:

```text
active == trading
```

Company status is a Companies House register concept, not necessarily a real-time statement of commercial activity.

## Addresses

Addresses are structured but contain optional fields.

Do not concatenate fields assuming every component exists.

## Dates

Some dates are partial.

DOB is a notable example.

## Previous names

A company can have multiple previous names.

Model them as a one-to-many relationship.

## SIC codes

A company can have multiple SIC codes.

Model them as a collection.

## Officers

A person can have multiple appointments.

Do not model an officer as belonging to exactly one company.

## PSCs

PSC records have lifecycle state.

Do not treat the endpoint as a static ownership table.

## Filing history

A filing represents a filing event/record, not necessarily the complete underlying document.

Follow the Document API link where a document is required.

---

# 37. Security considerations

The API itself is accessed over TLS, with Companies House recommending TLS 1.2.

Your application should:

- use HTTPS only
- store API keys in a secret manager
- avoid committing keys
- avoid putting keys in frontend code
- restrict key usage where appropriate
- rotate keys
- delete obsolete keys
- redact credentials from logs

For a backend application, authentication should happen server-side.

---

# 38. Testing strategy

Create tests for:

### Authentication

- valid key
- missing key
- invalid key

### HTTP behaviour

- 200
- 400
- 401
- 404
- 422
- 429
- 5xx

### Pagination

- zero results
- one page
- multiple pages
- exactly page-sized result
- final partial page

### Schema evolution

- unknown fields
- missing optional fields
- deprecated fields
- new enumeration value

### Data edge cases

- dissolved company
- company with previous names
- company with no officers
- company with many officers
- company with no PSC data
- company with multiple PSC records
- foreign company / UK establishment
- company with insolvency history
- paper filing
- filing without document metadata

---

# 39. Recommended Companies House client abstraction

A Python implementation could be structured as:

```text
companies_house/
├── client.py
├── auth.py
├── rate_limiter.py
├── retry.py
├── pagination.py
├── models/
│   ├── company.py
│   ├── officer.py
│   ├── filing.py
│   ├── charge.py
│   └── psc.py
├── endpoints/
│   ├── companies.py
│   ├── officers.py
│   ├── filings.py
│   ├── charges.py
│   └── psc.py
└── exceptions.py
```

The application should depend on your abstraction:

```python
company = companies_house.get_company(company_number)
```

rather than:

```python
requests.get(
    "https://api.company-information.service.gov.uk/company/..."
)
```

throughout the codebase.

---

# 40. Suggested initial endpoints

If starting a new project, I would implement these first:

## Phase 1 — core

```text
GET /company/{company_number}
GET /search/companies
GET /company/{company_number}/officers
GET /company/{company_number}/filing-history
GET /company/{company_number}/persons-with-significant-control
```

## Phase 2 — enrichment

```text
GET /company/{company_number}/charges
GET /company/{company_number}/insolvency
GET /company/{company_number}/registers
GET /company/{company_number}/uk-establishments
GET /officers/{officer_id}/appointments
```

## Phase 3 — document/data infrastructure

```text
GET /document/{document_id}
GET /document/{document_id}/content
```

## Phase 4 — large-scale ingestion

Investigate:

- Company Data Product
- PSC bulk data
- officer bulk products
- charges bulk products
- Streaming API

before scaling REST calls.

---

# 41. Recommended ingestion workflow

For an individual company:

```text
1. Resolve company name → company number
2. Get company profile
3. Store raw response + ETag
4. Extract resource links
5. Fetch required related resources
6. Paginate related lists
7. Store raw + normalised records
8. Record source retrieval timestamp
```

For a large dataset:

```text
1. Obtain bulk company snapshot
2. Load raw snapshot
3. Normalise company master
4. Add other bulk datasets as appropriate
5. Establish Streaming API consumer
6. Store last successful stream timepoint
7. Apply incremental events
8. Use REST for targeted enrichment only
```

---

# 42. What I would avoid

### Avoid 1 — API calls from the frontend

This exposes credentials and makes rate limiting difficult.

### Avoid 2 — One API key per worker

This creates an architecture that encourages rate-limit circumvention and makes quota management difficult.

### Avoid 3 — Full-register REST crawling

Use bulk products/streaming for large-scale workloads.

### Avoid 4 — Hard-coded response schemas

New fields can appear.

### Avoid 5 — Treating optional fields as mandatory

Companies House has many company types and data circumstances.

### Avoid 6 — Treating names as IDs

Use company numbers.

### Avoid 7 — Ignoring pagination

A first response is not necessarily the full list.

### Avoid 8 — Ignoring API versioning

Resource versions can change independently.

### Avoid 9 — Assuming "active" means financially healthy

It is a register status.

### Avoid 10 — Polling aggressively for changes

Use caching, ETags, bulk data or streaming where appropriate.

---

# 43. Practical decision tree

```text
Do I need one company?
        │
       YES
        │
   Company profile
        │
        ├── Need officers? → officers
        ├── Need filings?  → filing history
        ├── Need owners?   → PSC
        ├── Need debt?     → charges
        └── Need status?   → insolvency

Do I need to find a company?
        │
       YES
        │
   Search companies
        │
   obtain company_number
        │
   fetch company profile

Do I need thousands/millions of companies?
        │
       YES
        │
   Do not start with REST crawling
        │
        ├── Bulk snapshot
        └── Streaming updates

Do I need the actual filing document?
        │
       YES
        │
   Filing history
        ↓
   document_metadata
        ↓
   Document API
```

---

# 44. Key engineering conclusions

The Companies House API is straightforward to call, but the hard part is building a reliable integration around it.

The API itself is not the appropriate system of record for your application. Treat Companies House as an external source with:

- rate limits
- evolving schemas
- optional data
- pagination
- resource versioning
- transient failures
- data lifecycle semantics

The strongest implementation pattern is:

```text
                Companies House
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      Bulk          Stream          REST
        │             │             │
        └─────────────┼─────────────┘
                      ↓
              Ingestion layer
                      ↓
                Raw data store
                      ↓
              Normalisation
                      ↓
              Application DB
                      ↓
                 Your APIs
```

For a smaller application, start with the REST API and build the abstraction cleanly. If usage grows toward large-scale ingestion, introduce bulk snapshots and streaming rather than trying to scale REST requests indefinitely.

---

# 45. Sources consulted

Official Companies House sources:

1. Companies House Public Data API reference  
   https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference

2. Getting started  
   https://developer-specs.company-information.service.gov.uk/guides/gettingStarted

3. Authorisation  
   https://developer-specs.company-information.service.gov.uk/guides/authorisation

4. Developer guidelines  
   https://developer-specs.company-information.service.gov.uk/guides/developerGuidelines

5. Rate limiting  
   https://developer-specs.company-information.service.gov.uk/guides/rateLimiting

6. API versioning  
   https://developer-specs.company-information.service.gov.uk/guides/versioning

7. REST API introduction  
   https://developer-specs.company-information.service.gov.uk/guides/introduction

8. Document API  
   https://developer-specs.company-information.service.gov.uk/document-api/reference

9. Streaming API overview  
   https://developer-specs.company-information.service.gov.uk/streaming-api/guides/overview

10. Streaming API authentication  
    https://developer-specs.company-information.service.gov.uk/streaming-api/guides/authentication

11. Companies House data products  
    https://www.gov.uk/guidance/companies-house-data-products

12. Companies House developer API suite  
    https://developer-specs.company-information.service.gov.uk/

---

## Appendix A — Quick reference

### Base URL

```text
https://api.company-information.service.gov.uk
```

### Authentication

```text
HTTP Basic Auth
username = API key
password = empty
```

### Default rate limit

```text
600 requests / 5 minutes / application
```

### Most useful endpoints

```text
GET /search/companies
GET /company/{company_number}
GET /company/{company_number}/officers
GET /company/{company_number}/filing-history
GET /company/{company_number}/charges
GET /company/{company_number}/insolvency
GET /company/{company_number}/persons-with-significant-control
GET /officers/{officer_id}/appointments
```

### Core engineering rules

```text
Company number > company name
Bulk/streaming > REST for large-scale ingestion
Central rate limiter
Central retry policy
Central pagination
Store ETags
Store raw responses
Tolerate new fields
Handle optional fields
Monitor API changes
Never expose API keys to clients
```

**Status:** Engineering reference based on the official Companies House documentation available on 20 August 2026.
