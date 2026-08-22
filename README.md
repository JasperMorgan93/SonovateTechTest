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

```bash
pip install -e ".[dev]"
```

Set `COMPANIES_HOUSE_API_KEY` in your environment, then run:

```bash
python scripts/ingest_sono_search.py
```

This fetches every reachable page of `/search/companies?q=sono`, writes each raw page to
`src/company_data_platform/storage/bronze/ch_search_result/`, and prints the total number
of matching companies (tech test Question 1).

Run the test suite with:

```bash
pytest -v
```
