# SonovateTechTest

Answers the Sonovate Data & Analytics Engineer tech test using the Companies House
Public Data API — built as the first slice of a small local data platform (bronze/silver
layering, a reusable ingestion core, room to add more sources) rather than a one-off
script.

- **AI agent instructions (canonical, for any tool — Claude, Copilot, etc.):** [AGENTS.md](AGENTS.md)
- **Architecture, and why it's shaped this way:** [docs/architecture.md](docs/architecture.md)
- **Schema (bronze/silver, question → data mapping):** [docs/data-model.md](docs/data-model.md)
- **Individual design decisions:** [docs/adr/](docs/adr/)
- **Coding principles (for humans and agents working in this repo):** [docs/coding-principles.md](docs/coding-principles.md)
- **Engineering principles (how we work, beyond code):** [docs/engineering-principles.md](docs/engineering-principles.md)

## Setup & running

**Docker (no local Python required):**

```bash
cp .env.example .env   # then fill in COMPANIES_HOUSE_API_KEY
docker compose run --rm app
```

That one command runs the full pipeline — ingest (bronze), normalise (silver), then
analyse (gold) — and prints the answers to all six tech-test questions
(`scripts/run_all.py`). Bronze and silver data are written to `./data/` on the host
(mounted into the container), so re-running is idempotent and each stage's output
persists between runs.

Each stage can also be run on its own, e.g. to re-run just one step:

```bash
docker compose run --rm app scripts/ingest_sono_search.py     # bronze — fetches from the API
docker compose run --rm app scripts/normalise_sono_search.py  # silver — bronze -> canonical model
docker compose run --rm app scripts/analyse_sono_search.py    # gold — silver -> the six answers
```

After changing `src/`, `scripts/`, `pyproject.toml`, or `uv.lock`, rebuild the image before
running again:

```bash
docker compose build          # cache-aware — only rebuilds the layers that changed
docker compose build --no-cache   # full rebuild from scratch, ignoring cache
docker compose up --build     # rebuild and run in one step
```

**Local (non-Docker) dev, using [uv](https://docs.astral.sh/uv/):**

```bash
uv sync --extra dev
```

Set `COMPANIES_HOUSE_API_KEY` in your environment, then run the whole pipeline:

```bash
uv run python scripts/run_all.py
```

or each stage individually:

```bash
uv run python scripts/ingest_sono_search.py
uv run python scripts/normalise_sono_search.py
uv run python scripts/analyse_sono_search.py
```

Run the test suite with:

```bash
uv run pytest -v
```
