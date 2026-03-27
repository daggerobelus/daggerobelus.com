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

## Step 2: Compute CER with the Script

**Do not compute CER yourself.** Use the deterministic Python script. This ensures every evaluation produces exactly the same number for the same inputs — a requirement for reproducibility.

```bash
python skills/manuscript-evaluation/scripts/compute_cer.py \
  <reference-file> <hypothesis-file> --verbose
```

The script handles all normalization deterministically:
1. Strips confidence markers (`[word?]` → `word`)
2. Strips and counts illegibility markers (`[...]`)
3. Normalizes whitespace
4. Preserves everything else (spelling, punctuation, capitalization, u/v, i/j)
5. Computes Levenshtein edit distance at the character level

It outputs JSON with:
- `cer` / `cer_percent` — the Character Error Rate
- `coverage` — what fraction of the reference the agent actually attempted (vs. marking `[...]`)
- `substitutions`, `insertions`, `deletions` — the edit operations
- `reference_characters`, `hypothesis_characters` — character counts
- `gap_count`, `uncertain_count` — how many `[...]` and `[word?]` markers

**Both CER and coverage matter.** A transcription that's 99% accurate but only covers 40% of the page isn't useful. Report both numbers prominently.

**Benchmarks for context:**
- < 1% CER = very good
- < 5% CER = usable for most research purposes
- ~3% CER = Transkribus Egerton model (best existing for English secretary hand)
- > 10% CER = significant errors, needs investigation

**If CER is below 3%, flag for review.** The best honest blind result in this project is 3.80%. A result substantially below that is not impossible, but requires the integrity audit (in the test-run skill) to confirm clean conditions before it can be reported as a genuine improvement.

## Step 3: Categorize Errors

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

## Step 4: Write the Evaluation Report

Produce a single file: `[manuscript]-evaluation.txt`

Structure:

```
# Evaluation: [manuscript name and page]

## CER Summary (from compute_cer.py)
- Reference characters: N
- Hypothesis characters: N
- Substitutions: N | Insertions: N | Deletions: N
- **CER: X.XX%**
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
- **Do not guess at error causes based on the manuscript content.** You can't see the manuscript. Categorize based on the textual evidence: if "vpon" became "upon," that's modernization regardless of what the letterforms look like.
