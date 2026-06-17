from pathlib import Path

import ledger


def test_append_and_read_roundtrip(tmp_path):
    run = tmp_path / "run-1"
    run.mkdir()
    ledger.append_result(str(run), 1, "naive seed", 0.21, 0.19, True, "iterations/iter-01/method.md")
    ledger.append_result(str(run), 2, "add long-s note", 0.23, 0.20, False, "")
    rows = ledger.read_results(str(run))
    assert len(rows) == 2
    assert rows[0]["iter"] == 1
    assert rows[0]["val_diplomatic_cer"] == 0.21
    assert rows[0]["kept"] is True
    assert rows[1]["kept"] is False


def test_best_so_far_ignores_reverted(tmp_path):
    run = tmp_path / "run-1"
    run.mkdir()
    ledger.append_result(str(run), 1, "a", 0.21, 0.19, True, "p1")
    ledger.append_result(str(run), 2, "b", 0.10, 0.09, False, "")   # reverted -> ignored
    ledger.append_result(str(run), 3, "c", 0.18, 0.16, True, "p3")
    assert ledger.best_so_far(str(run)) == (0.18, 3)


def test_best_so_far_none_when_empty(tmp_path):
    run = tmp_path / "run-1"
    run.mkdir()
    assert ledger.best_so_far(str(run)) is None


def test_snapshot_method_copies_file(tmp_path):
    run = tmp_path / "run-1"
    run.mkdir()
    method = run / "method.md"
    method.write_text("Transcribe this page.")
    path = ledger.snapshot_method(str(run), 7, str(method))
    assert Path(path).read_text() == "Transcribe this page."
    assert path.endswith("iterations/iter-07/method.md")
