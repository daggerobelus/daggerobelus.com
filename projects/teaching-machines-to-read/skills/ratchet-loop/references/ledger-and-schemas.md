# Config, Ledger, Schemas & Resume

Everything the loop needs to be auditable and resumable lives in a `ratchet/` directory in the repo.

## `ratchet/config.yaml`

Pinned in Phase 0, coauthored with the user. Example for a transcription skill specialized to one
scribal hand (deliberately non-code, to show the suite is general):

```yaml
objective:                                # a weighted benchmark suite, not a single number
  protocol: "python bench/score.py --pages evals/dev --seed 7"   # pinned; comparable every round
  replicates: 3
  metrics:
    - { name: char_accuracy,   direction: maximize, weight: 0.5, floor_tolerance: 0.0 }
    - { name: word_accuracy,   direction: maximize, weight: 0.3, floor_tolerance: 0.01 }
    - { name: layout_fidelity, direction: maximize, weight: 0.2, floor_tolerance: 0.02 }
  composite: weighted_geometric_mean      # default: punishes any single weak column (the krausest way)
  normalize: factor_vs_best                # each metric as a factor vs best-known; keeps score scale-free
  # weighted sum is available but only use it when metrics are genuinely substitutable.
  # floor_tolerance: a candidate that regresses this metric past tolerance fails — reserve floors for
  # hard binary limits; the geometric mean already handles "don't let any column rot."

mode: specialist            # specialist: fitting to the shots is the goal. generalist: must transfer.

gates:                      # hard invariants beyond the suite; fail any -> ineligible
  - { name: no_memorized_outputs, check: "python bench/anti_memo.py" }   # specialist degeneracy guard
  - { name: runs_on_full_page,    check: "python bench/smoke.py" }

surfaces:
  mutable: ["skill/transcribe/**", "skill/glyph_rules/**"]
  frozen:  ["bench/**", "evals/**", "ratchet/**"]    # validator, data, gates, config — untouchable

evaluation:
  dev_set: "evals/dev/*"
  holdout_set: "evals/holdout/*"      # specialist: SAME hand, unseen pages (catches memorization)
  holdout_sampling: same_distribution # generalist would use: transfer
  confirm_on_holdout: every_promotion

topology: single_lineage     # or: { type: island, islands: 4, migrate_every: 5 }

goal:                        # keep the orchestrator out of Sisyphus — name a finishable target
  season_target: { composite: 0.92 }    # provisional if the true goal is "as good as possible"
  season_round_budget: 12               # a season ends here even without hitting target
  on_season_end: summarize_and_offer_new_season

budgets:
  fanout: { min: 4, max: 8 }
  max_rounds: 50
  max_cost_usd: 40
  candidate_timeout_s: 600

exit_criteria:
  target: { composite: 0.95 }   # optional; omit if "as good as possible"
  plateau_patience: 6
  epsilon: 0.003                 # composite units; below this a "win" is convergence noise
  # plus always: budget exhausted, or user stop

strategy:
  initial_mix: { refine: 2, tune: 1, subtract: 1, first_principles: 1, cross_pollinate: 1 }
  reallocation_damping: auto      # tie shift rate to the measured noise band
```

The `frozen` list explicitly naming `bench/`, `evals/`, and `ratchet/` is the tamper guard. If any of
those overlap the mutable globs, the loop is unsound — resolve it before starting. Note how `mode:
specialist` reshapes `holdout_sampling` (same-hand unseen pages) and adds an anti-memorization gate
rather than penalizing the tight fit itself.

## `ratchet/ledger.jsonl`

Append-only, one JSON object per round. It is three things at once: the bandit's memory, the human's
audit trail, and the resume point. Never rewrite it; only append.

```json
{
  "round": 12,
  "baseline_commit": "a1b9f3c",
  "baseline_metric": { "composite": 0.871, "submetrics": { "char_accuracy": 0.93, "word_accuracy": 0.81, "layout_fidelity": 0.84 }, "spread": 0.004 },
  "noise_band_sigma": 0.005,
  "candidates": [
    { "branch": "r12-c0", "archetype": "refine", "instance": "tighten long-s disambiguation rule",
      "diff_summary": "skill/glyph_rules/longs.md +12 -7", "metric": { "composite": 0.884, "spread": 0.004 },
      "gates": "pass", "floors": "pass", "disposition": "eligible" },
    { "branch": "r12-c1", "archetype": "first_principles", "instance": "rebuild abbreviation expansion from contraction grammar",
      "diff_summary": "skill/transcribe/abbrev.* +130 -84", "metric": { "composite": 0.908, "spread": 0.006 },
      "gates": "pass", "floors": "pass", "disposition": "promoted",
      "confirm": { "rerun_composite": 0.906, "holdout_composite": 0.901 } },
    { "branch": "r12-c2", "archetype": "subtract", "instance": "drop the post-hoc spellcheck pass",
      "diff_summary": "skill/transcribe/post.* +0 -41", "metric": { "composite": 0.889, "spread": 0.005 },
      "gates": "pass", "floors": "word_accuracy:FAIL (-0.03 > 0.01 tol)", "disposition": "disqualified:floor" },
    { "branch": "r12-c3", "archetype": "wildcard", "instance": "edited bench/score.py weights",
      "disposition": "disqualified:tamper", "note": "touched frozen surface bench/score.py" }
  ],
  "promotion": { "branch": "r12-c1", "new_baseline": "c7e2d10",
    "justification": "0.908 vs 0.871 baseline; margin 0.037 >> 0.005σ; survived rerun and same-hand holdout" },
  "archive_top_m": ["r12-c0"],
  "archetype_yield_update": { "first_principles": "+1 promote, avg_margin 7.8" },
  "exit_check": "continue"
}
```

The `disqualified:tamper` entry is the point of the audit — that candidate edited the scorer and was
caught before its number could count.

## Resume protocol

To restart a loop that was interrupted:

1. Read `config.yaml` and the last ledger line. The last `promotion.new_baseline` (or `baseline_commit`
   if the last round promoted nothing) is the current baseline — check it out.
2. Rebuild archetype yield stats by folding over the ledger (it's the full history).
3. Reconstruct the archive from the most recent `archive_top_m` whose branches still exist; if pruned,
   the ledger's diff summaries are enough to regenerate equivalents.
4. Continue at Phase 1, step 1, with the recovered baseline and yield stats.

Because every promotion is a real commit and every decision is in the ledger, the loop is fully
reconstructible — there is no hidden in-memory state that a crash can lose.

## A note on the noise band

`noise_band_sigma` is the spine of the promotion rule, so estimate it honestly. Cheapest source: the
run-to-run spread of the baseline, re-measured every round (replicates give you this for free). If the
metric is very noisy, raise `replicates` or the promotion z-threshold rather than accepting marginal
wins — a margin below the band is the loop's most common way to quietly ratchet backward.
