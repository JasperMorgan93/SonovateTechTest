from scripts import run_all


def test_main_runs_ingest_then_normalise_then_analyse_in_order(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(run_all, "ingest", lambda: calls.append("ingest"))
    monkeypatch.setattr(run_all, "normalise", lambda: calls.append("normalise"))
    monkeypatch.setattr(run_all, "analyse", lambda: calls.append("analyse"))

    run_all.main()

    assert calls == ["ingest", "normalise", "analyse"]
