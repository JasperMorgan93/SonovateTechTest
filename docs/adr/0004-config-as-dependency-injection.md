# ADR 0004: Configuration is injected via typed config objects, not read ad-hoc

**Status:** Accepted

## Context

Rate limit, retry behaviour, timeouts, base URL and endpoint paths could each be read
from environment variables or module-level constants at the point they're used. That's
the fastest way to write a script, but it makes the client hard to reuse: every test
needs real env vars or monkeypatching, and every new deployment (or a second source
reusing the same REST machinery) means editing source rather than passing arguments.

## Decision

Define typed config objects (`RateLimitConfig`, `RetryConfig`, `RestSourceConfig`, and
per-source configs like `CompaniesHouseConfig`) in `core/config.py` and alongside each
source. Clients, ingestion methods, and normalisers take their config as a constructor
argument. A top-level `Settings` (pydantic-settings) reads environment variables / `.env`
once, at the composition root (the CLI entrypoint), and builds the config objects passed
down to everything else. No class reaches into `os.environ` or a global settings object
directly.

## Consequences

- Unit tests construct small, fast configs (tiny rate limit, zero backoff, a mock base
  URL) directly, with no environment setup and no real sleeping in retry tests.
- Changing the rate limit, pointing at a sandbox base URL, or renaming an endpoint path is
  a config change, not a code change.
- A second REST source built on `RestIngestionMethod` gets the same injectable shape for
  free, and there's a clear place (`RestSourceConfig`) documenting what a REST source's
  config is expected to contain.
- Slightly more boilerplate up front (defining config classes) than reading `os.getenv()`
  inline. Accepted, since it's what makes `core/` and `ingestion/` importable as a library
  rather than a script coupled to one process's environment.
