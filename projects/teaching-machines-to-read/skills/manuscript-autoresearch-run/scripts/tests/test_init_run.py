import json
from pathlib import Path

import init_run


def test_naive_seed_and_structure(tmp_path):
    run = init_run.init_run(str(tmp_path), "smoke", "blind", "naive",
                            splits_root=str(tmp_path / "corpus_root"), max_iters=2, patience=1)
    run = Path(run)
    assert run == tmp_path / "runs" / "smoke"
    assert (run / "method.md").read_text() == init_run.NAIVE_METHOD
    cfg = json.loads((run / "config.json").read_text())
    assert cfg["arm"] == "blind" and cfg["start_mode"] == "naive"
    assert cfg["max_iters"] == 2 and cfg["patience"] == 1
    for sub in ("iterations", "hyp", "final-test-eval"):
        assert (run / sub).is_dir()


def test_best_seed_copies_transcription_skill(tmp_path):
    run = Path(init_run.init_run(str(tmp_path), "seeded", "faithful", "best",
                                 splits_root=str(tmp_path / "corpus_root")))
    method = (run / "method.md").read_text()
    # the best-method seed is the manuscript-transcription SKILL.md — non-trivial, not the naive line
    assert method != init_run.NAIVE_METHOD
    assert len(method) > 200


def test_bad_arm_or_start_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        init_run.init_run(str(tmp_path), "x", "sideways", "naive", splits_root="r")
    with pytest.raises(ValueError):
        init_run.init_run(str(tmp_path), "x", "blind", "fancy", splits_root="r")
