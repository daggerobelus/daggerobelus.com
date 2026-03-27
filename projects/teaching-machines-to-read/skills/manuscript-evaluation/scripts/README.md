# Evaluation Scripts

Deterministic tools for measuring manuscript transcription accuracy. These scripts are the measurement instruments for the Teaching Machines to Read project — they must produce exactly the same output every time for the same inputs.

## Setup

```bash
pip install -r requirements.txt
```

Dependencies: `jiwer` (the standard HTR/OCR evaluation library, used in Transkribus benchmarks and ICDAR competitions), `numpy`, `scipy`.

## Scripts

### compute_cer.py

Computes Character Error Rate between a reference and hypothesis transcription using `jiwer`.

```bash
# Full JSON output
python compute_cer.py reference.txt hypothesis.txt

# Just the CER number (for scripting)
python compute_cer.py reference.txt hypothesis.txt --raw

# With normalization details
python compute_cer.py reference.txt hypothesis.txt --verbose
```

**Output fields:**

| Field | Type | Meaning |
|---|---|---|
| `cer` | decimal | CER as a decimal (e.g., `0.0912` = 9.12%) |
| `cer_percent` | string | CER as a percentage string |
| `coverage` | decimal | Fraction of reference text the agent attempted (1.0 = everything) |
| `substitutions` | integer | Characters replaced with a different character |
| `insertions` | integer | Characters in hypothesis not in reference |
| `deletions` | integer | Characters in reference missing from hypothesis |
| `reference_characters` | integer | Total chars in normalized reference |
| `hypothesis_characters` | integer | Total chars in normalized hypothesis |
| `gap_count` | integer | Number of `[...]` illegibility markers found |
| `uncertain_count` | integer | Number of `[word?]` uncertainty markers found |
| `normalization_log` | list | Every normalization action taken |

### compute_stats.py

Computes publication-ready statistics for a set of CER values using `scipy.stats`.

```bash
# From command line values
python compute_stats.py 9.12 10.45 8.87 11.20 9.55

# From a run results JSON file
python compute_stats.py --from-json run-14-results.json
```

**Output fields:**
- `cer.mean`, `cer.median` — central tendency
- `cer.std_dev` — sample standard deviation (Bessel-corrected)
- `cer.ci_95_lower`, `cer.ci_95_upper` — 95% confidence interval (t-distribution, appropriate for small N)
- `cer.min`, `cer.max`, `cer.spread_pp` — range
- `cer.iqr_lower`, `cer.iqr_upper` — interquartile range (25th–75th percentile)

## Normalization Pipeline

Both scripts apply these normalization steps in order before comparison:

1. **Strip confidence markers** — `[word?]` → `word`, `{context: ...}` removed
2. **Strip illegibility markers** — `[...]` removed and counted for coverage, `[b....es]` → `bes`
3. **Normalize whitespace** — collapse multiple spaces, trim lines

**Preserved (not touched):** original spelling, punctuation, capitalization, line breaks, u/v, i/j, long-s, doubled consonants, terminal -e. No orthographic normalization of any kind.

## Reproducibility

These scripts are fully deterministic. The same inputs will always produce exactly the same outputs. There is no randomness, no AI judgment, and no model calls. They are the reproducible measurement instruments for the experiment — the "ruler" must not change between measurements.
