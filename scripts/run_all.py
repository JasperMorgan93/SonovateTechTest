"""Run the full pipeline — ingest, normalise, then analyse — in one command.

Run with: python scripts/run_all.py

Convenience wrapper for a single-command Docker/local run: chains
`ingest_sono_search.py` (bronze), `normalise_sono_search.py` (silver), and
`analyse_sono_search.py` (gold + the six test-spec answers), in that order.
Each step is independently runnable too — see the scripts' own docstrings.
"""

from scripts.analyse_sono_search import main as analyse
from scripts.ingest_sono_search import main as ingest
from scripts.normalise_sono_search import main as normalise


def main() -> None:
    """Run ingestion, then normalisation, then analysis, printing each step's report in turn."""
    ingest()
    print()
    normalise()
    print()
    analyse()


if __name__ == "__main__":
    main()
