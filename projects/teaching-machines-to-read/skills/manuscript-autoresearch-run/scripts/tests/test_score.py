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
