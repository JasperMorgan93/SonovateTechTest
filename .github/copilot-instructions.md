# GitHub Copilot instructions

The canonical instructions for this repository live in [AGENTS.md](../AGENTS.md) — read it, and everything it links to (`docs/coding-principles.md`, `docs/engineering-principles.md`, `docs/architecture.md`, `docs/adr/`), before making changes. This file is a pointer, not a separate rulebook — do not add Copilot-specific conventions here that diverge from `AGENTS.md`; fix `AGENTS.md` instead so every agent stays in sync.

Key rules to apply on every suggestion, summarised from `AGENTS.md`:

- Follow `docs/coding-principles.md` without exception — readability first, DRY, YAGNI, no magic literals, no hardcoded paths/credentials, explicit signatures, type hints and docstrings, tests for every change.
- Check `docs/adr/` before proposing a new structural pattern.
- Keep changes scoped to what was asked.
