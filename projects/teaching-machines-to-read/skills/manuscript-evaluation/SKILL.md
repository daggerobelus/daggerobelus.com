---
name: manuscript-evaluation
description: >
  Evaluate a manuscript transcription against a reference by computing Character
  Error Rate (CER) and categorizing errors. Use this skill when you need to grade
  a transcription, compare it against ground truth, compute CER, or analyze
  transcription errors. Also use when asked to evaluate paleographic accuracy or
  assess transcription quality.
---

# Manuscript Evaluation — Blind CER Assessment

## Research Context

This evaluation is part of a digital humanities research project whose results will be presented to scholars. Methodological rigor is not optional — it's the entire point.

**Use the provided scripts for all quantitative measurement.** CER must be computed by `compute_cer.py` (which uses `jiwer`, the field-standard HTR evaluation library), not estimated or calculated by hand. Statistical summaries must be computed by `compute_stats.py` (which uses `scipy.stats`). Your job is the qualitative error categorization — the part that requires intelligence and judgment. The numbers come from deterministic, reproducible scripts that a reviewer can verify independently.

## Your Task

You are evaluating a transcription of an early modern manuscript page by comparing it against a human-made reference transcription. Your job has two parts:

1. **Compute CER deterministically** using the Python script (reproducible, reviewer-defensible)
2. **Categorize errors qualitatively** using your judgment (the part that benefits from intelligence)

**You are intentionally blind.** You do not see the original manuscript image. This is by design — it prevents you from re-reading the manuscript and unconsciously adjusting your evaluation. You compare text against text, nothing more.

## Your Materials

- **Hypothesis transcription** — the transcription to evaluate (produced by a transcription agent)
- **Reference transcription** — the ground truth (from FromThePage or another human transcription source)
- **CER script** — `skills/manuscript-evaluation/scripts/compute_cer.py`

You should NOT have access to:
- The original manuscript image
- The paleography guide
- The vocabulary reference
- The transcription agent's alphabet chart
- Any other agent's work

If you can see any of these, flag it immediately. Your evaluation is only valid if you are blind to the source material.

## Step 1: Verify File Contents

Before running any computation, quickly confirm that both input files contain what you expect:

1. **Check the hypothesis file** — it should contain only transcription text (no headers, section markers like `===`, metadata, or confidence notes). If it contains extra content, flag it immediately — the CER script compares character-by-character and extra text will produce wildly inflated error rates.
2. **Check the reference file** — it may have a header block above a `---` separator (the script strips this automatically). The text below the separator should be the ground truth transcription.

If either file looks wrong (e.g., the hypothesis contains `=== TRANSCRIPTION ===` section markers or appended notes), stop and report the problem rather than running the script on bad input.

## Step 2: Clean transcription-extraneous markup (reference AND hypothesis)

Reference transcriptions carry markup that a paleographic transcription deliberately omits — and if it is left in, every bit of it counts as a CER "error" the transcriber never actually made. This was a real, uncaught source of **~2.5–3 points of inflation** in this project's earlier evaluations. Strip it from BOTH files before measuring, so CER reflects *reading accuracy* (did the agent get the words right), not formatting or lineation fidelity.

**First, run the deterministic cleaner on both files** — it handles the known artifacts reproducibly:

```bash
python skills/manuscript-evaluation/scripts/clean_reference.py <reference-file>  <reference-file>.clean
python skills/manuscript-evaluation/scripts/clean_reference.py <hypothesis-file> <hypothesis-file>.clean
```

It strips: FromThePage recipe-segment counters `(1)`, brace annotations `{page break}`, standalone page/recipe numbers and roman-numeral lines, end-of-line hyphenation (`Worm-\nwood` → `Wormwood`), and it flattens all whitespace to single spaces (so double-spacing and line-break differences do not count — we are not measuring lineation).

**Then use judgment for what the script can't anticipate.** Different sources leave different residue — EMROC, Folger DOCX, and other references carry markup the regexes don't know about (editorial sigla, folio/shelfmark stamps, catalog numbers, `[note: …]` annotations, marginal-reference markers). Read both cleaned files; remove only what is *unambiguously not part of the manuscript text*.

**Cardinal rule of this step: when in doubt, keep it.** Over-cleaning — deleting real text, the scribe's punctuation, or a genuine orthographic feature — corrupts the measurement far worse than a stray marker left in. You strip *markup*, never *text*. Never touch spelling, words, capitalization, or the scribe's own punctuation.

**Log every removal you make beyond the script** (the exact strings and why), so a reviewer can confirm nothing substantive was touched. This log goes in the report. All CER in the next step runs on the `.clean` files.

## Step 3: Compute CER with the Script (on the cleaned files)

**Do not compute CER yourself.** Use the deterministic Python script on the cleaned files from Step 2. This ensures every evaluation produces exactly the same number for the same inputs — a requirement for reproducibility.

```bash
python skills/manuscript-evaluation/scripts/compute_cer.py \
  <reference-file>.clean <hypothesis-file>.clean --verbose
```

The script handles all normalization deterministically:
1. Strips confidence markers (`[word?]` → `word`)
2. Strips and counts illegibility markers (`[...]`)
3. Normalizes whitespace
4. Preserves everything else (spelling, punctuation, capitalization, u/v, i/j)
5. Computes Levenshtein edit distance at the character level

It outputs JSON with:
- `cer` / `cer_percent` — the Character Error Rate (overall, including gap-caused deletions)
- `attempted_cer` / `attempted_cer_percent` — CER on confident text only (excludes deletions from `[...]` gaps). This measures: "when the agent says it can read something, how often is it right?"
- `coverage` — what fraction of the reference the agent actually attempted (vs. marking `[...]`)
- `substitutions`, `insertions`, `deletions` — the edit operations
- `reference_characters`, `hypothesis_characters` — character counts
- `gap_count`, `uncertain_count` — how many `[...]` and `[word?]` markers

**Three metrics matter together:**
1. **Coverage** — how much did the agent attempt? (lower = more honest about limits)
2. **Attempted CER** — of what it attempted, how accurate was it? (the confidence-calibration measure)
3. **Overall CER** — the combined picture including gaps

An agent with 80% coverage and 3% attempted CER is more useful than one with 100% coverage and 17% overall CER — the first gives you reliable text with clearly marked gaps a human can fill in.

**Benchmarks for context:**
- < 1% CER = very good
- < 5% CER = usable for most research purposes
- ~3% CER = Transkribus Egerton model (trained on 2,500+ pages of one specific hand)
- ~5–8% CER = Transkribus Titan general model (no hand-specific training)
- > 10% CER = significant errors, needs investigation

**Note on Transkribus comparison:** The ~3% Egerton benchmark required thousands of pages of hand-labeled ground truth in one specific hand. This project's approach uses zero training data — a fundamentally different method. Results near or below the Titan general model (~5–8%) with zero training data are strong; results near the Egerton model (~3%) with zero training data are exceptional.

**If CER is below 3%, flag for review.** The best honest blind result in this project is 3.80%. A result substantially below that is not impossible, but requires the integrity audit (in the test-run skill) to confirm clean conditions before it can be reported as a genuine improvement.

**Treat historical figures as not directly comparable.** Cleaning measurably lowered CER on this project's Sedley material (~2.5–3 points), so a cleaned CER is not on the same scale as an uncleaned one. The older project figures (3.80%, the Transkribus comparisons, etc.) predate this pipeline and their exact computation/normalization is uncertain — they may not have been produced through this skill at all — so do not rank a cleaned CER against them. To compare against any historical result, re-run that result through this pipeline (Step 2 + Step 3) so both numbers are computed the same way. Always note in the report that the CER is post-cleaning.

## Step 4: Categorize Errors

This is where your judgment matters. The script tells you *how many* errors there are; you figure out *what kind* and *why*.

Align the hypothesis against the reference and classify each error. These categories come from patterns observed across multiple blind transcription experiments:

### Error Categories

| Category | Description | Example |
|---|---|---|
| **Modernization** | Agent replaced early modern spelling with modern equivalent | "vpon" → "upon", "haue" → "have" |
| **Archaization** | Agent used a *more* archaic form than the reference — over-applying early modern conventions | "use" → "vse", "upon" → "vppon" |
| **Letterform confusion** | Agent misidentified a letter (e.g., long-s/f, c/r, e/o) | "ſeeth" → "feeth", "sauce" → "sauer" |
| **Hallucination** | Agent fabricated text not present in the manuscript | Entire phrases with no basis in the image |
| **Normalization** | Agent regularized orthography the scribe used inconsistently | Doubled consonants singled, terminal -e dropped |
| **Abbreviation** | Agent missed, misread, or incorrectly expanded an abbreviation | "-es graph" missed, thorn not recognized |
| **Word substitution** | Agent replaced an unfamiliar word with a familiar one | Archaic term → modern synonym |
| **Omission** | Agent skipped text that is present in the reference | Missing words or lines |
| **Addition** | Agent added text not in the reference | Extra words, repeated lines |
| **Punctuation/formatting** | Differences in punctuation, capitalization, or line breaks | Missing periods, wrong capitalization |

For each error, record:
- The reference text
- The hypothesis text
- The category
- The approximate line number
- A brief note on what likely went wrong

### Aggregate Summary

After listing individual errors, provide counts per category and note:
- Which category accounts for the most errors
- Whether errors cluster in a particular section of the manuscript (beginning, middle, end)
- Any patterns that suggest a systematic problem (e.g., the agent consistently misreads one letter)

## Step 5: Write the Evaluation Report

Produce a single file: `[manuscript]-evaluation.txt`

Structure:

```
# Evaluation: [manuscript name and page]

## Cleaning Log (Step 2)
- Deterministic cleaner: applied to reference and hypothesis (clean_reference.py)
- Additional removals by judgment: [exact strings removed and why — or "none"]
- Confirmation: no spelling, words, capitalization, or scribal punctuation altered
- CER below is POST-cleaning (not comparable to pre-cleaning historical figures)

## CER Summary (from compute_cer.py, on cleaned files)
- Reference characters: N
- Hypothesis characters: N
- Substitutions: N | Insertions: N | Deletions: N
- **CER: X.XX%** (overall)
- **Attempted CER: X.XX%** (confident text only — excludes gap-caused deletions)
- **Coverage: XX.X%** (fraction of reference text the agent attempted)
- Gaps ([...]): N | Uncertain ([word?]): N

## Error Breakdown
| Category | Count | % of Total Errors |
|----------|-------|--------------------|
| ...      | ...   | ...                |

## Individual Errors
[list each error with line number, reference text, hypothesis text, category, and note]

## Patterns and Observations
[aggregate analysis — what went wrong systematically, where errors cluster,
what a revised transcription approach might focus on]
```

## What Not to Do

- **Do not compute CER yourself.** Use the script. Your mental math is not reproducible; the script is.
- **Do not look at the manuscript image.** Your job is text-against-text comparison. If you see the image, your evaluation is compromised.
- **Do not penalize honest gaps.** An agent that writes `[...]` for an illegible passage made the right call. The script handles this — gaps are stripped before CER and tracked as coverage.
- **Do not "fix" either transcription.** Compare them as-is. Your job is measurement, not correction.
- **Do not over-clean.** In Step 2 you strip *markup*, never *text*. When unsure whether something is a stray artifact or part of the manuscript, keep it and log the uncertainty — deleting real text corrupts the measurement worse than a leftover marker.
- **Do not guess at error causes based on the manuscript content.** You can't see the manuscript. Categorize based on the textual evidence: if "vpon" became "upon," that's modernization regardless of what the letterforms look like.
