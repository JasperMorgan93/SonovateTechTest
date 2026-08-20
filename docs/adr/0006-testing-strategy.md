# ADR 0006: TDD for components, BDD for the test questions

**Status:** Accepted

## Context

The test spec explicitly asks for TDD/BDD practice, not just correct answers. The six
questions are also, conveniently, a ready-made set of acceptance criteria — each one is a
testable statement about the data.

## Decision

- **TDD** for everything below the acceptance layer: `core/` (rate limiter, retry,
  paginator) and the normaliser are written test-first, against mocked HTTP (`responses`)
  and recorded fixture payloads (`tests/fixtures/`). No unit test calls the real API.
- **BDD** for the six questions themselves: one Gherkin scenario per question in
  `tests/features/`, run with `pytest-bdd`, exercised against the real ingest→normalise
  pipeline running over fixture HTTP responses and a real (test) Postgres instance. These
  are the acceptance criteria for the whole task, expressed in the same language as the
  spec.
- Live-API integration tests exist separately, gated behind `--run-live` and a real API
  key. They are never run by default or in CI — they exist to validate assumptions about
  the real API's shape occasionally, not to gate every run.

## Consequences

- The six questions are executable, not just answered by hand — running the BDD suite is
  itself evidence the answers in `ANSWERS.md` are correct for the fixture data, and the
  same suite catches a regression if the normaliser changes.
- Fixture payloads need to be representative of real Companies House responses (dissolved
  company, limited-partnership, multiple SIC codes, partial address, multi-page search),
  or the BDD suite proves nothing beyond "the code does what the fixtures say."
- Two testing styles in one repo (plain pytest for units, pytest-bdd for acceptance) is
  slightly more setup than picking one, but keeps unit tests fast/granular while keeping
  the six questions readable as scenarios rather than buried in assertions.
