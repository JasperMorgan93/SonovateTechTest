# Coding Principles

These principles apply across the entire repository — to every component and language — for both human contributors and AI coding agents. They are deliberately stack-agnostic; component-level `AGENTS.md` files add stack-specific conventions on top of these, and must not contradict them.

For the reasoning behind these rules, and guidance when a situation isn't covered here, see [Engineering Principles](./engineering-principles.md).

## Core Principles

### Readability first
Code is read far more often than it is written. Prefer clear, self-documenting names over brevity or cleverness.

### DRY — search before you write
Before writing new logic, search for an existing implementation (a shared base class, utility module, or helper). Duplication is a defect, not a shortcut — if similar logic exists in two places, consolidate it before adding a third. Even comments can be seen as breaking the DRY principle. If a comment is required to explain the code, it shouldn't exist. The code should be written clearly - Readability first.

### YAGNI
Don't build abstractions, configuration options, or generalisations for requirements that don't exist yet.

### Single responsibility & composition over duplication
Model shared behaviour through base classes, mixins, or shared utilities. A class or function should only contain what is genuinely specific to it — prefer overriding one method over copying and modifying a whole class.

A function that's grown long is almost always a function doing more than one job — treat length as a smell, not just a style nit. If a function mixes distinct steps (e.g. building a query, validating the result, and logging), split each step into its own named, independently testable method rather than leaving them inlined together.

### Explicit signatures over broad `**kwargs`
Prefer explicit, typed, named parameters with visible defaults over accepting `**kwargs` and pulling values out via `kwargs.get(key, default)` inside the body. A reader should be able to tell what a function accepts — and what's required vs. optional — from the signature alone, without tracing through base classes or grepping for `.get(`. Reserve `**kwargs` for genuine pass-through cases (e.g. forwarding to a parent constructor).

### Explicit inputs/outputs over hidden state
Prefer methods that take their data as parameters and return their result over methods that silently read and mutate instance attributes (e.g. `self.do_something()` with no arguments or return value). A reader should be able to tell what a method uses and produces from its signature alone, without opening the body to trace which attributes it touches. Reserve implicit `self` state for genuine object identity/config, not for passing data between steps of a workflow.

### No magic literals
Repeated literal strings or numbers (column names, status codes, path segments, config keys) must be extracted into named constants or enums rather than inlined.

### No hardcoded paths, credentials, or environment-specific values
Use the component's existing configuration/secrets/path abstractions (for example `Namespace`/`PathManager` in `data_processing`, Django settings/env vars in `metastore`, Key Vault in `power-bi` deployment scripts). Never hardcode a secret, connection string, or environment-specific path.

### No raw, string-built SQL
Use parameterised queries, an ORM, or a DataFrame API. String-concatenated SQL is a defect, not a convenience, unless genuinely unavoidable — and then the reason must be justified inline.

### Type hints & docstrings (Python)
- All new public function, method, and class signatures must have type hints.
- All new public functions, methods, and classes need a docstring (Google style). Private helpers (`_prefixed`) don't strictly require one but should have descriptive names.
- This applies to any signature you add or modify — including in otherwise-untyped legacy files. Don't extend an untyped method without adding hints to it; don't use "the rest of the file is untyped" as a reason to skip it.

### Error handling
- Fail loudly. Never swallow exceptions with a bare `except:` — catch specific exceptions.
- Error messages and logs must never leak secrets, credentials, or PII.

### Security
- Validate untrusted input at system boundaries (API views, file ingestion, external calls).
- Never commit secrets, tokens, or credentials — use the environment's secret manager.
- Enforce authentication/authorization checks at both the entry point and query/data-access level.

### Testing
- Add or update tests for every behaviour change or bug fix.
- Tests must be isolated, deterministic, and independent of real external systems (mount points, live databases, production catalogs) — inject test doubles/fixtures instead.
- One logical behaviour per test; use descriptive names (e.g. `test_<method>_<scenario>_<expected_outcome>`).

### Scoped changes
Keep changes focused on what was asked. Avoid unrelated refactors or drive-by formatting of code you weren't asked to touch.

### Documentation
Update the relevant `AGENTS.md`/README when public behaviour, interfaces, or operational commands change.

## Enforcement

Automate what can be automated; treat the rest as a mandatory review responsibility.
