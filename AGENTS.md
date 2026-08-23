# AGENTS.md

Canonical entry point for AI coding agents (Claude, GitHub Copilot, Cursor, or anything else) working in this repository. Tool-specific files — `CLAUDE.md`, `.github/copilot-instructions.md`, and any others — exist only to point back here. This file is the single source of truth; keep instructions in one place, not duplicated across tool configs.

## Read before you start

- [docs/coding-principles.md](docs/coding-principles.md) — the standing brief for how code is written. Follow it without exception.
- [docs/engineering-principles.md](docs/engineering-principles.md) — the reasoning behind those rules, and the guide for situations they don't explicitly cover.
- [docs/architecture.md](docs/architecture.md) — the shape of this system and why.
- [docs/data-model.md](docs/data-model.md) — schema, question → data mapping.
- [docs/adr/](docs/adr/) — individual structural decisions. Check here before introducing a new pattern; the decision may already be made.

## Ground rules

- Follow [docs/coding-principles.md](docs/coding-principles.md) for every change, in every language, in every component.
- Component-level `AGENTS.md` files (none exist yet) may add stack-specific conventions on top of this file, but must never contradict it.
- When a situation isn't covered by the coding principles, reason from [docs/engineering-principles.md](docs/engineering-principles.md) rather than inventing a new convention.
- Keep changes scoped to what was asked — see "Scoped changes" in the coding principles.
- Structural or cross-cutting decisions get an ADR (`docs/adr/`), not a comment or a one-off choice buried in code.
- Update the relevant docs (this file, `docs/`, `README.md`) when behaviour, interfaces, or conventions change.
- Whenever structural changes in the code base or routes occur - always re-read AGENT and README files and see if the information no longer aligns to the code. If so, raise this with the user to correct it.
- The Docker image is not rebuilt automatically. After changing `src/`, `scripts/`, `pyproject.toml`, or `uv.lock`, run `docker compose build` before verifying behaviour via `docker compose run --rm app` — otherwise you're testing stale code baked into the last image.

## Repo map

- `src/company_data_platform/` — `ingestion` (bulk, rest, streaming), `transform` (canonical), `storage`, `analytics`, `core`
- `scripts/` — standalone entry-point scripts (not part of the installable package), e.g. `ingest_sono_search.py`
- `tests/` — `unit`, `features`, `fixtures`
- `docs/` — architecture, data model, ADRs, coding/engineering principles
- `Dockerfile`, `docker-compose.yml` — containerised run path (`docker compose run --rm app`), no local Python required
- `pyproject.toml` + `uv.lock` — dependency management via [uv](https://docs.astral.sh/uv/) (`uv sync --extra dev`), not `pip`/Poetry
