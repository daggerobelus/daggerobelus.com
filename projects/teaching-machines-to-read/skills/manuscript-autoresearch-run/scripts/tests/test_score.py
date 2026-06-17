from collections import Counter

import score


def test_char_edits_counts_one_substitution():
    e = score.char_edits("cat", "cot")
    assert e["subs"] == 1 and e["ins"] == 0 and e["dels"] == 0
    assert e["ref_len"] == 3
    assert e["sub_pairs"] == Counter({("a", "o"): 1})


def test_score_pages_aggregates_edit_weighted():
    # page A: 1 sub in 3 chars; page B: perfect in 4 chars.
    # aggregate diplomatic CER = 1 / (3+4) = 0.142857
    out = score.score_pages([("cat", "cot"), ("good", "good")])
    assert round(out["diplomatic_cer"], 6) == round(1 / 7, 6)
    assert out["n_pages"] == 2


def test_reading_cer_forgives_u_v_modernization():
    # "vse" vs "use": diplomatic counts the v->u as an error; reading forgives it.
    out = score.score_pages([("vse", "use")])
    assert out["diplomatic_cer"] > 0
    assert out["reading_cer"] == 0.0
    assert out["normalization_gap"] == out["diplomatic_cer"] - out["reading_cer"]


def test_error_profile_is_single_chars_only():
    out = score.score_pages([("vse vpon", "use upon")])
    prof = out["error_profile"]
    # private aggregation keys must not leak
    assert "_sub_pairs" not in out
    # every reported token is exactly one display character (no words leak)
    for r, h, _c in prof["top_substitutions"]:
        assert len(r) == 1 and len(h) == 1
    for ch, _c in prof["top_deletions"] + prof["top_insertions"]:
        assert len(ch) == 1
    # v->u substitution is the dominant diplomatic error here
    assert ["v", "u", 2] in prof["top_substitutions"]


def test_profile_lists_capped_at_25():
    # 30 distinct substitutions; profile keeps the top 25
    ref = "".join(chr(ord('a') + i) for i in range(30))   # abc...
    hyp = "".join(chr(ord('A') + i) for i in range(30))   # ABC...
    out = score.score_pages([(ref, hyp)])
    assert len(out["error_profile"]["top_substitutions"]) == 25


import json
from pathlib import Path

import build_splits


def _seed_split(tmp_path):
    src = tmp_path / "src"
    root = tmp_path / "root"
    src.mkdir()
    # minimal real-shaped corpus for the val split only
    for n in build_splits.SPLITS["val"]:
        (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"J")
        (src / f"sedley-ms534-page{n}-transcription.txt").write_text("the quick broun fox")
    for n in build_splits.SPLITS["dev"] + build_splits.SPLITS["test"]:
        (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"J")
        (src / f"sedley-ms534-page{n}-transcription.txt").write_text("x")
    build_splits.build(str(src), str(root))
    return root


def test_score_split_runs_and_stays_blind(tmp_path):
    root = _seed_split(tmp_path)
    hyp = tmp_path / "hyp"
    hyp.mkdir()
    for n in build_splits.SPLITS["val"]:
        (hyp / f"page-{n}.txt").write_text("the quick brown fox")  # broun->brown modernization-ish

    out = score.score_split(str(root), "val", str(hyp))
    assert out["split"] == "val" and out["n_pages"] == 13
    assert out["missing_hypotheses"] == []

    # BLINDNESS: no reference word appears anywhere in the serialized output
    blob = json.dumps(out)
    for word in ["quick", "broun", "brown", "fox"]:
        assert word not in blob


def test_score_split_raises_on_missing_splits_json(tmp_path):
    import pytest
    nonexistent = tmp_path / "no_such_root"
    with pytest.raises(ValueError, match="splits.json"):
        score.score_split(str(nonexistent), "val", str(tmp_path / "hyp"))


def test_score_split_raises_on_unknown_split(tmp_path):
    import pytest
    root = _seed_split(tmp_path)
    with pytest.raises(ValueError, match="not a key"):
        score.score_split(str(root), "unknown_split", str(tmp_path / "hyp"))


def test_score_split_raises_on_missing_refs_dir(tmp_path):
    import pytest
    root = _seed_split(tmp_path)
    import shutil
    shutil.rmtree(root / "corpus" / "val" / "refs")
    with pytest.raises(ValueError, match="refs"):
        score.score_split(str(root), "val", str(tmp_path / "hyp"))


def test_missing_hypothesis_counts_as_deletions(tmp_path):
    root = _seed_split(tmp_path)
    hyp = tmp_path / "hyp"
    hyp.mkdir()
    # provide only one page; the other 12 are missing
    n0 = build_splits.SPLITS["val"][0]
    (hyp / f"page-{n0}.txt").write_text("the quick broun fox")
    out = score.score_split(str(root), "val", str(hyp))
    assert len(out["missing_hypotheses"]) == 12
    assert out["diplomatic_cer"] > 0  # missing pages are all-deletions
