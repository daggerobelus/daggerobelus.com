# Autoresearch Eval & Corpus Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic, testable measurement foundation for the autoresearch CER-optimization experiment: a frozen corpus split, a sealed blind scorer, and a results ledger.

**Architecture:** Three small Python modules under a new `manuscript-autoresearch-run` skill's `scripts/` directory. `build_splits.py` copies the Sedley corpus into an isolated dev/val/test layout. `score.py` reuses the existing `clean_reference.py` cleaning functions and `jiwer` to return *only* aggregate CER numbers plus a blind character-level error profile — never reference text. `ledger.py` records the ratchet (results.tsv + per-iteration method snapshots). This plan is data/code only; the agent-driven optimizer loop that *consumes* this infrastructure is Plan 2.

**Tech Stack:** Python 3, `jiwer` (already a project dependency), `pytest` (test runner).

## Global Constraints

- **Blindness is the cardinal rule.** `score.py`'s machine-readable output MUST contain only numbers and single-character error counts. It MUST NOT contain any multi-character reference word, line, or phrase. A leak here invalidates the experiment's treatment arm. One task explicitly asserts this.
- **Cleaning is reused, not reinvented.** Diplomatic cleaning = `clean()` and reading normalization = `reading_normalize()`, both imported from `skills/manuscript-evaluation/scripts/clean_reference.py`. Do not duplicate that logic.
- **Primary metric = diplomatic CER** (punishes modernization bias). Reading CER is logged alongside; the gap is reported.
- **Frozen splits.** The dev/val/test page assignments are fixed literals (below) and must not be regenerated randomly. Same split for all four runs.
- **CER aggregation is edit-weighted:** aggregate CER = `sum(S+I+D over pages) / sum(reference_chars over pages)`, never the mean of per-page CERs.
- **Manuscript source:** `projects/teaching-machines-to-read/ingest/archive/sedley-ms534-full/`, files named `sedley-ms534-page{NNN}.jpg` and `sedley-ms534-page{NNN}-transcription.txt` (NNN zero-padded, e.g. `004`).
- **All paths below are relative to the project root** `projects/teaching-machines-to-read/` unless absolute.
- **Frozen split (13/13/13), page numbers:**
  - dev: `003 006 009 012 015 018 021 024 027 030 033 036 039`
  - val: `004 007 010 013 016 019 022 025 028 031 034 037 041`
  - test: `005 008 011 014 017 020 023 026 029 032 035 038 042`

---

## File Structure

```
projects/teaching-machines-to-read/
├── skills/manuscript-autoresearch-run/scripts/
│   ├── build_splits.py        # Task 1 — freeze + copy corpus into isolated layout
│   ├── score.py               # Tasks 2–4 — sealed blind scorer
│   ├── ledger.py              # Task 5 — results.tsv + method snapshots
│   ├── requirements.txt       # Task 1 — jiwer, pytest
│   └── tests/
│       ├── test_build_splits.py
│       ├── test_score.py
│       └── test_ledger.py
└── ingest/archive/test/autoresearch-sedley-01/   # DATA artifacts (created by build_splits.py)
    ├── splits.json
    └── corpus/{dev, val/images, val/refs, test/images, test/refs}/
```

The reusable code lives in the skill; the experiment's data artifacts live under `ingest/archive/test/` per the project's test-isolation rule. Scorer imports cleaning from the sibling `manuscript-evaluation` skill (single source of truth).

---

### Task 1: Frozen split builder

**Files:**
- Create: `skills/manuscript-autoresearch-run/scripts/build_splits.py`
- Create: `skills/manuscript-autoresearch-run/scripts/requirements.txt`
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_build_splits.py`

**Interfaces:**
- Consumes: nothing (entry point).
- Produces:
  - `SPLITS: dict[str, list[str]]` — module-level frozen split (keys `"dev"`, `"val"`, `"test"`; values lists of zero-padded page strings).
  - `build(source_dir: str, out_root: str) -> dict` — copies files into the isolated layout and writes `splits.json`; returns the manifest dict it wrote.
  - Layout written under `out_root`: `corpus/dev/page-{NNN}.jpg` + `corpus/dev/page-{NNN}.txt`; `corpus/val/images/page-{NNN}.jpg` + `corpus/val/refs/page-{NNN}.txt`; same for `test`. `splits.json` at `out_root`.

- [ ] **Step 1: Create `requirements.txt`**

```
jiwer>=3.0
pytest>=8.0
```

- [ ] **Step 2: Write the failing test**

`skills/manuscript-autoresearch-run/scripts/tests/test_build_splits.py`:

```python
import json
from pathlib import Path

import build_splits


def _make_fake_corpus(src: Path):
    """One .jpg + one -transcription.txt for every page in all three splits."""
    src.mkdir(parents=True, exist_ok=True)
    for pages in build_splits.SPLITS.values():
        for n in pages:
            (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"JPEGDATA")
            (src / f"sedley-ms534-page{n}-transcription.txt").write_text(f"ref {n}")


def test_splits_are_13_each_and_disjoint():
    s = build_splits.SPLITS
    assert [len(s["dev"]), len(s["val"]), len(s["test"])] == [13, 13, 13]
    allp = s["dev"] + s["val"] + s["test"]
    assert len(allp) == len(set(allp)) == 39
    assert "002" not in allp  # flyleaf excluded


def test_build_copies_isolated_layout(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    _make_fake_corpus(src)

    manifest = build_splits.build(str(src), str(out))

    # val images present, val refs present, but images dir has NO refs (isolation)
    val_imgs = sorted(p.name for p in (out / "corpus/val/images").glob("*"))
    val_refs = sorted(p.name for p in (out / "corpus/val/refs").glob("*"))
    assert val_imgs == [f"page-{n}.jpg" for n in build_splits.SPLITS["val"]]
    assert val_refs == [f"page-{n}.txt" for n in build_splits.SPLITS["val"]]
    assert not list((out / "corpus/val/images").glob("*.txt"))

    # dev keeps image + ref together (study pool)
    assert (out / "corpus/dev/page-003.jpg").exists()
    assert (out / "corpus/dev/page-003.txt").exists()

    # manifest written and matches
    written = json.loads((out / "splits.json").read_text())
    assert written == manifest
    assert written["splits"] == build_splits.SPLITS
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_build_splits.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_splits'`.

- [ ] **Step 4: Write `build_splits.py`**

```python
#!/usr/bin/env python3
"""
build_splits.py — freeze the Sedley dev/val/test split and copy it into an
isolated layout for the autoresearch experiment.

Isolation is deliberate: val/test images and references live in SEPARATE
folders so a transcriber subagent can be handed images with no path to the
answers. dev keeps image+ref together because dev is the study pool.

Usage:
    python build_splits.py SOURCE_DIR OUT_ROOT
    # SOURCE_DIR e.g. ingest/archive/sedley-ms534-full
    # OUT_ROOT   e.g. ingest/archive/test/autoresearch-sedley-01
"""
import json
import shutil
import sys
from pathlib import Path

# Frozen split — DO NOT regenerate randomly. Same for all four runs.
SPLITS = {
    "dev":  ["003", "006", "009", "012", "015", "018", "021", "024", "027", "030", "033", "036", "039"],
    "val":  ["004", "007", "010", "013", "016", "019", "022", "025", "028", "031", "034", "037", "041"],
    "test": ["005", "008", "011", "014", "017", "020", "023", "026", "029", "032", "035", "038", "042"],
}

MANUSCRIPT = "sedley-ms534"


def _src_img(src: Path, n: str) -> Path:
    return src / f"{MANUSCRIPT}-page{n}.jpg"


def _src_ref(src: Path, n: str) -> Path:
    return src / f"{MANUSCRIPT}-page{n}-transcription.txt"


def build(source_dir: str, out_root: str) -> dict:
    src = Path(source_dir)
    out = Path(out_root)

    for n in SPLITS["dev"]:
        dst = out / "corpus" / "dev"
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_src_img(src, n), dst / f"page-{n}.jpg")
        shutil.copyfile(_src_ref(src, n), dst / f"page-{n}.txt")

    for split in ("val", "test"):
        imgs = out / "corpus" / split / "images"
        refs = out / "corpus" / split / "refs"
        imgs.mkdir(parents=True, exist_ok=True)
        refs.mkdir(parents=True, exist_ok=True)
        for n in SPLITS[split]:
            shutil.copyfile(_src_img(src, n), imgs / f"page-{n}.jpg")
            shutil.copyfile(_src_ref(src, n), refs / f"page-{n}.txt")

    manifest = {
        "manuscript": MANUSCRIPT,
        "excluded": ["002"],
        "splits": SPLITS,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "splits.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: build_splits.py SOURCE_DIR OUT_ROOT", file=sys.stderr)
        sys.exit(1)
    m = build(sys.argv[1], sys.argv[2])
    print(json.dumps(m, indent=2))
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_build_splits.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Build the real corpus and eyeball it**

Run (from project root `projects/teaching-machines-to-read/`):
```bash
python skills/manuscript-autoresearch-run/scripts/build_splits.py \
  ingest/archive/sedley-ms534-full \
  ingest/archive/test/autoresearch-sedley-01
ls ingest/archive/test/autoresearch-sedley-01/corpus/val/images | wc -l   # -> 13
ls ingest/archive/test/autoresearch-sedley-01/corpus/val/refs   | wc -l   # -> 13
ls ingest/archive/test/autoresearch-sedley-01/corpus/val/images/*.txt 2>/dev/null | wc -l  # -> 0 (isolation)
```
Expected: 13, 13, 0.

- [ ] **Step 7: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/build_splits.py \
        skills/manuscript-autoresearch-run/scripts/requirements.txt \
        skills/manuscript-autoresearch-run/scripts/tests/test_build_splits.py \
        ingest/archive/test/autoresearch-sedley-01/splits.json
git commit -m "feat(autoresearch): frozen Sedley dev/val/test split builder"
```

> Note: commit `splits.json` but NOT the copied corpus images/refs (they are derived from the in-repo source). Add `ingest/archive/test/autoresearch-sedley-01/corpus/` to `.gitignore` in this task if the repo does not already ignore large image copies — check `git status` and ignore the `corpus/` path if it shows up.

---

### Task 2: Scorer core — aggregate diplomatic + reading CER

**Files:**
- Create: `skills/manuscript-autoresearch-run/scripts/score.py`
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_score.py`

**Interfaces:**
- Consumes: `clean()` and `reading_normalize()` from `skills/manuscript-evaluation/scripts/clean_reference.py` (imported via sys.path).
- Produces:
  - `char_edits(ref: str, hyp: str) -> dict` — returns `{"subs": int, "ins": int, "dels": int, "ref_len": int, "sub_pairs": Counter, "ins_chars": Counter, "del_chars": Counter}` for two already-cleaned strings.
  - `score_pages(pairs: list[tuple[str, str]]) -> dict` — `pairs` is `[(ref_text, hyp_text), ...]` (raw, uncleaned). Returns the metrics dict described below (error profile added in Task 3).

- [ ] **Step 1: Write the failing test**

`skills/manuscript-autoresearch-run/scripts/tests/test_score.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'score'`.

- [ ] **Step 3: Write `score.py` (core only — profile comes in Task 3)**

```python
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


def score_pages(pairs) -> dict:
    dipl_cer, dipl_pp, sub_pairs, ins_chars, del_chars = _aggregate(pairs, reading=False)
    read_cer, read_pp, _, _, _ = _aggregate(pairs, reading=True)
    return {
        "n_pages": len(pairs),
        "diplomatic_cer": round(dipl_cer, 6),
        "reading_cer": round(read_cer, 6),
        "normalization_gap": round(dipl_cer - read_cer, 6),
        "per_page_diplomatic": dipl_pp,
        "per_page_reading": read_pp,
        # error profile attached in Task 3 via _profile(...)
        "_sub_pairs": sub_pairs,
        "_ins_chars": ins_chars,
        "_del_chars": del_chars,
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/score.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_score.py
git commit -m "feat(autoresearch): aggregate diplomatic + reading CER scorer core"
```

---

### Task 3: Blind error profile

**Files:**
- Modify: `skills/manuscript-autoresearch-run/scripts/score.py` (add `_profile`, fold into `score_pages`)
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_score.py` (add cases)

**Interfaces:**
- Consumes: the `_sub_pairs`/`_ins_chars`/`_del_chars` Counters produced by Task 2's `score_pages`.
- Produces: `score_pages` now returns an `"error_profile"` key and drops the private `_*` keys. Shape:
  `{"top_substitutions": [["v","u",14], ...], "top_deletions": [["'",9], ...], "top_insertions": [[" ",3], ...]}` — each char is a single display character (space rendered as `"␣"`). Lists capped at 25 entries, descending by count.

- [ ] **Step 1: Write the failing test (append to test_score.py)**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py::test_error_profile_is_single_chars_only -v`
Expected: FAIL — `KeyError: 'error_profile'`.

- [ ] **Step 3: Add `_profile` and fold into `score_pages`**

Add to `score.py`:

```python
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
```

Replace the `return {...}` at the end of `score_pages` with:

```python
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/score.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_score.py
git commit -m "feat(autoresearch): blind single-char error profile"
```

---

### Task 4: Sealed scorer CLI + blindness assertion

**Files:**
- Modify: `skills/manuscript-autoresearch-run/scripts/score.py` (add file-loading + CLI)
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_score.py` (add CLI/leak test)

**Interfaces:**
- Consumes: `splits.json` + `corpus/<split>/refs/page-{NNN}.txt` from a splits root; hypotheses as `page-{NNN}.txt` in a hypothesis dir.
- Produces:
  - `score_split(splits_root: str, split: str, hyp_dir: str) -> dict` — loads ref/hyp file pairs for the split (in split page order) and returns `score_pages(...)` plus `"split"` and `"missing_hypotheses"` (page numbers with no hyp file, scored as empty hypothesis = all deletions).
  - CLI: `python score.py --splits-root R --split val --hyp-dir D` → prints the result JSON to stdout (the optimizer's only view).

- [ ] **Step 1: Write the failing test (append)**

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py::test_score_split_runs_and_stays_blind -v`
Expected: FAIL — `AttributeError: module 'score' has no attribute 'score_split'`.

- [ ] **Step 3: Add file-loading + CLI to `score.py`**

```python
def score_split(splits_root: str, split: str, hyp_dir: str) -> dict:
    root = Path(splits_root)
    manifest = json.loads((root / "splits.json").read_text())
    pages = manifest["splits"][split]
    refs_dir = root / "corpus" / split / "refs"
    hyp = Path(hyp_dir)

    pairs = []
    missing = []
    for n in pages:
        ref_text = (refs_dir / f"page-{n}.txt").read_text(errors="replace")
        hyp_path = hyp / f"page-{n}.txt"
        if hyp_path.exists():
            hyp_text = hyp_path.read_text(errors="replace")
        else:
            hyp_text = ""          # missing = empty hypothesis = all deletions
            missing.append(n)
        pairs.append((ref_text, hyp_text))

    result = score_pages(pairs)
    result["split"] = split
    result["missing_hypotheses"] = missing
    return result


def main():
    import argparse
    p = argparse.ArgumentParser(description="Sealed blind scorer (numbers + single-char profile only).")
    p.add_argument("--splits-root", required=True)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--hyp-dir", required=True)
    args = p.parse_args()
    print(json.dumps(score_split(args.splits_root, args.split, args.hyp_dir), indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_score.py -v`
Expected: PASS (all tests, including the blindness and missing-hypothesis cases).

- [ ] **Step 5: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/score.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_score.py
git commit -m "feat(autoresearch): sealed scorer CLI with blindness + missing-page handling"
```

---

### Task 5: Results ledger + method snapshots

**Files:**
- Create: `skills/manuscript-autoresearch-run/scripts/ledger.py`
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_ledger.py`

**Interfaces:**
- Consumes: nothing from other tasks (standalone; the optimizer in Plan 2 calls it).
- Produces:
  - `RESULTS_HEADER = ["iter", "change_description", "val_diplomatic_cer", "val_reading_cer", "kept", "snapshot_path"]`
  - `append_result(run_dir, iter_n, change_description, dipl_cer, read_cer, kept, snapshot_path) -> None` — appends a tab-separated row, writing the header first if the file is new.
  - `read_results(run_dir) -> list[dict]` — parses results.tsv into row dicts (numbers as floats, `kept` as bool).
  - `best_so_far(run_dir) -> tuple[float, int] | None` — lowest `val_diplomatic_cer` among rows where `kept` is True, with its iter; `None` if no kept rows.
  - `snapshot_method(run_dir, iter_n, method_path) -> str` — copies `method_path` to `run_dir/iterations/iter-{NN}/method.md` (NN zero-padded width 2) and returns that path.

- [ ] **Step 1: Write the failing test**

`skills/manuscript-autoresearch-run/scripts/tests/test_ledger.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_ledger.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ledger'`.

- [ ] **Step 3: Write `ledger.py`**

```python
#!/usr/bin/env python3
"""
ledger.py — the ratchet record for an autoresearch run.

results.tsv is the append-only log (one row per iteration). Each KEPT
iteration also snapshots method.md into iterations/iter-NN/ so the winning
method at every step is recoverable — the "git ratchet" as plain folders.
"""
import shutil
from pathlib import Path

RESULTS_HEADER = ["iter", "change_description", "val_diplomatic_cer",
                  "val_reading_cer", "kept", "snapshot_path"]


def _results_path(run_dir: str) -> Path:
    return Path(run_dir) / "results.tsv"


def append_result(run_dir, iter_n, change_description, dipl_cer, read_cer, kept, snapshot_path) -> None:
    path = _results_path(run_dir)
    new = not path.exists()
    # tabs/newlines would corrupt the TSV; collapse them in free text.
    desc = " ".join(str(change_description).split())
    row = [str(iter_n), desc, f"{dipl_cer:.6f}", f"{read_cer:.6f}",
           "1" if kept else "0", snapshot_path]
    with path.open("a", encoding="utf-8") as f:
        if new:
            f.write("\t".join(RESULTS_HEADER) + "\n")
        f.write("\t".join(row) + "\n")


def read_results(run_dir) -> list:
    path = _results_path(run_dir)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines[1:]:  # skip header
        if not line.strip():
            continue
        cells = line.split("\t")
        rows.append({
            "iter": int(cells[0]),
            "change_description": cells[1],
            "val_diplomatic_cer": float(cells[2]),
            "val_reading_cer": float(cells[3]),
            "kept": cells[4] == "1",
            "snapshot_path": cells[5] if len(cells) > 5 else "",
        })
    return rows


def best_so_far(run_dir):
    kept = [r for r in read_results(run_dir) if r["kept"]]
    if not kept:
        return None
    best = min(kept, key=lambda r: r["val_diplomatic_cer"])
    return (best["val_diplomatic_cer"], best["iter"])


def snapshot_method(run_dir, iter_n, method_path) -> str:
    dst_dir = Path(run_dir) / "iterations" / f"iter-{int(iter_n):02d}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "method.md"
    shutil.copyfile(method_path, dst)
    return str(dst)
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest tests/test_ledger.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Run the whole suite**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python -m pytest -v`
Expected: PASS (all tests across the three test files).

- [ ] **Step 6: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/ledger.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_ledger.py
git commit -m "feat(autoresearch): results ledger + per-iteration method snapshots"
```

---

## What this plan delivers

After Task 5, the experiment has a working, tested measurement core: a frozen isolated Sedley split on disk, a sealed scorer that turns a folder of hypothesis transcriptions into blind CER numbers + a single-character error profile (with a test proving no reference word leaks), and a ledger that records the ratchet. Plan 2 builds the agent-driven optimizer loop and the runner skill on top of these interfaces (`build_splits.SPLITS`, `score.score_split`, `ledger.append_result/best_so_far/snapshot_method`).

## Self-Review

- **Spec coverage:** frozen 13/13/13 split with isolation (Task 1 — spec §3); sealed evaluator returning cleaned diplomatic + reading CER + blind error profile (Tasks 2–4 — spec §4.2); results.tsv + iteration snapshots (Task 5 — spec §4.4). The optimizer loop, the two arms, the stopping rule, and the runner skill (spec §2, §5, §6, §8) are deliberately deferred to Plan 2 and named as such.
- **Blindness (spec §10):** Task 4 Step 1 asserts no reference word appears in the serialized scorer output; Task 3 asserts every profile token is a single character.
- **Placeholder scan:** none — every code step shows complete code; every run step shows the command and expected result.
- **Type consistency:** `score_pages` → `score_split` reuse the same dict; `error_profile` shape is identical across Tasks 3–4; `ledger` function names match the Interfaces blocks and the Plan-2 handoff note.
