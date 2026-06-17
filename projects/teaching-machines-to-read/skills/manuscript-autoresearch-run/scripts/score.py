#!/usr/bin/env python3
"""
score.py — sealed blind scorer for the autoresearch experiment.

Returns ONLY numbers and single-character error counts. Never emits a
multi-character reference word, line, or phrase. This is what an optimizer
agent is allowed to see; the blindness is the experiment's treatment.

Diplomatic = structural cleaning only (clean()); preserves orthography.
Reading    = clean() + reading_normalize(); forgives modernization that keeps
             word identity. The gap is the cost of modernization.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import jiwer

# Single source of truth for cleaning: the evaluation skill's functions.
_EVAL_SCRIPTS = Path(__file__).resolve().parents[2] / "manuscript-evaluation" / "scripts"
sys.path.insert(0, str(_EVAL_SCRIPTS))
from clean_reference import clean, reading_normalize  # noqa: E402


def char_edits(ref: str, hyp: str) -> dict:
    """Character-level edit counts + per-operation character tallies for two
    ALREADY-CLEANED strings, using jiwer's alignment."""
    subs = ins = dels = 0
    sub_pairs: Counter = Counter()
    ins_chars: Counter = Counter()
    del_chars: Counter = Counter()

    if len(ref) == 0:
        ins = len(hyp)
        for c in hyp:
            ins_chars[c] += 1
        return {"subs": subs, "ins": ins, "dels": dels, "ref_len": 0,
                "sub_pairs": sub_pairs, "ins_chars": ins_chars, "del_chars": del_chars}

    out = jiwer.process_characters(ref, hyp)
    ref_chars = out.references[0]
    hyp_chars = out.hypotheses[0]
    subs, ins, dels = out.substitutions, out.insertions, out.deletions

    for chunk in out.alignments[0]:
        if chunk.type == "substitute":
            for r, h in zip(ref_chars[chunk.ref_start_idx:chunk.ref_end_idx],
                            hyp_chars[chunk.hyp_start_idx:chunk.hyp_end_idx]):
                sub_pairs[(r, h)] += 1
        elif chunk.type == "insert":
            for h in hyp_chars[chunk.hyp_start_idx:chunk.hyp_end_idx]:
                ins_chars[h] += 1
        elif chunk.type == "delete":
            for r in ref_chars[chunk.ref_start_idx:chunk.ref_end_idx]:
                del_chars[r] += 1

    return {"subs": subs, "ins": ins, "dels": dels, "ref_len": len(ref_chars),
            "sub_pairs": sub_pairs, "ins_chars": ins_chars, "del_chars": del_chars}


def _aggregate(pairs, reading: bool):
    tot_e = tot_ref = 0
    sub_pairs: Counter = Counter()
    ins_chars: Counter = Counter()
    del_chars: Counter = Counter()
    per_page = []
    for ref_raw, hyp_raw in pairs:
        ref_c = clean(ref_raw)
        hyp_c = clean(hyp_raw)
        if reading:
            ref_c = reading_normalize(ref_c)
            hyp_c = reading_normalize(hyp_c)
        e = char_edits(ref_c, hyp_c)
        errs = e["subs"] + e["ins"] + e["dels"]
        tot_e += errs
        tot_ref += e["ref_len"]
        page_cer = errs / e["ref_len"] if e["ref_len"] else 0.0
        per_page.append(round(page_cer, 6))
        sub_pairs += e["sub_pairs"]
        ins_chars += e["ins_chars"]
        del_chars += e["del_chars"]
    cer = tot_e / tot_ref if tot_ref else 0.0
    return cer, per_page, sub_pairs, ins_chars, del_chars


def _disp(c: str) -> str:
    """Render a single character for the profile; spaces become a visible glyph."""
    return "␣" if c == " " else ("⏎" if c == "\n" else c)


def _profile(sub_pairs, ins_chars, del_chars, top: int = 25) -> dict:
    return {
        "top_substitutions": [[_disp(r), _disp(h), n]
                              for (r, h), n in sub_pairs.most_common(top)],
        "top_deletions": [[_disp(c), n] for c, n in del_chars.most_common(top)],
        "top_insertions": [[_disp(c), n] for c, n in ins_chars.most_common(top)],
    }


def score_pages(pairs) -> dict:
    dipl_cer, dipl_pp, sub_pairs, ins_chars, del_chars = _aggregate(pairs, reading=False)
    read_cer, read_pp, _, _, _ = _aggregate(pairs, reading=True)
    result = {
        "n_pages": len(pairs),
        "diplomatic_cer": round(dipl_cer, 6),
        "reading_cer": round(read_cer, 6),
        "normalization_gap": round(dipl_cer - read_cer, 6),
        "per_page_diplomatic": dipl_pp,
        "per_page_reading": read_pp,
        "error_profile": _profile(sub_pairs, ins_chars, del_chars),
    }
    return result
