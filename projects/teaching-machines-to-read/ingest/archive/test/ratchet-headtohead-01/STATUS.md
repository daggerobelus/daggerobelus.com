# Ratchet head-to-head — STATUS (paused 2026-07-02)

Head-to-head experiment: **ratchet-loop (plain)** vs **ratchet-loop-forum** optimizing
blind diplomatic CER on Lady Sedley MS534. The only variable between arms is the forum's
argumentative layer (experimenters predict effects, argumentative credit, an independent
**challenger** that can veto a promotion the number alone would wave through). Autonomous —
no human in either loop.

## What is built and saved (all durable, in the repo)
- **Skills installed:** `skills/ratchet-loop/` and `skills/ratchet-loop-forum/` (SKILL.md +
  references/). These are the two designs under test, from the zips Sarah downloaded.
- **Isolated workspace:** `ingest/archive/test/ratchet-headtohead-01/`
  - `splits.json` + `corpus/` are **symlinks** to `autoresearch-sedley-01` (same frozen
    dev/val/test 3-way split, read-only — clean comparability, separate artifacts).
  - `plain/config.yaml`, `forum/config.yaml` — the pinned Phase-0 setup contracts (identical
    except forum's `strategy.credit: argumentative` + `review` challenger block).
  - `ratchet-headtohead.workflow.js` — the runner (faithful implementation of both skills).
  - `plain/rounds/`, `forum/rounds/` — experimenter method.md outputs + hyp transcriptions.
  - `run-outputs/` — (intended for rescued run JSONs; /tmp was cleared before rescue — see below).

## Objective (pinned, both arms)
- Minimize **diplomatic CER** on 13 val pages, measured BLIND (image only). Reading CER is a
  guard floor. Mutable surface = the transcription `method.md` only. Frozen = scorer, images,
  refs, splits, configs, ledgers. Baseline = naive one-liner. Specialist mode (tune to Sedley's
  hand); dev = val, held-out = test. Promotion = beat baseline by > noise band (3 replicates,
  median-based) AND survive a fresh-rerun + held-out-test confirmation.

## Findings so far
1. **Pipeline is sound** (dry-run w9hnadzcc): experimenters edit the method, blind transcribe +
   score work, forum challenger fires, gates/paths function.
2. **Naive baseline is already ~7% diplomatic CER** — Opus is a strong reader even with a
   one-sentence instruction. Best round-1 single-edit candidates reached ~6.5%. **Modest but
   real headroom** (~7% → plausibly ~4–5% over 10 accumulating rounds).
3. **Dominant noise source was occasional incomplete-page transcription** (a transcriber
   stopping halfway down a page → that page scores ~50% CER → swings the aggregate ~5pp). FIXED:
   (a) hard "transcribe the COMPLETE page top to bottom" instruction; (b) 3 baseline replicates
   with a median-based robust noise band so one truncated replicate can't poison the baseline.

## Two bugs found in full-run attempt 1 (ww818rl6f) — one fixed, one external
- **[FIXED] Target-above-baseline early exit.** `target` was 0.08 but the naive baseline is
  ~0.069, so `plain` "hit target" and exited after round 1 having optimized nothing. Fixed:
  default target lowered to **0.045** (below the naive floor) AND target-exit now requires
  `promotions > 0`. (See `ratchet-headtohead.workflow.js`.)
- **[EXTERNAL] Session/credit limit.** The `forum` arm hit the account session limit mid-run;
  every forum agent errored, so forum produced no result (best_val_dipl defaulted to 1.0).
  Nothing to fix in code — just needs a rerun with budget available.

**Net: attempt 1 produced no usable optimization result.** `plain` = 1 empty round then early
exit (target bug); `forum` = all agents failed on credits. The value so far is the
infrastructure + the findings above, all of which are saved.

## Where the lost data went (and why it doesn't matter)
The top-level run summary JSONs were written to `/tmp/.../tasks/*.output`, which was cleared
when the session rolled over. But: (a) that run produced no usable result, and (b) the
per-agent transcripts persist at
`~/.claude/projects/-Users-sarahbonanno-daggerobelus-com/f904f77b-.../subagents/workflows/wf_221dfe10-205/`
if any detail is ever needed. All experimenter method outputs + transcriptions persist in the
workspace.

## To resume / rerun (after credits reset)
The partial run is not cleanly resumable across a session change, and attempt 1 had no useful
state, so **rerun fresh** rather than resuming:
```
Workflow({ scriptPath: ".../ratchet-headtohead-01/ratchet-headtohead.workflow.js",
           args: { dry_run: false } })
```
Defaults now: max_rounds 10, fanout 6, plateau_patience 3, epsilon 0.005, target 0.045.
Expect a few hours and several hundred agents across both arms. Round 1 of the live run doubles
as a final pipeline check (visible in the ledger). When it finishes: write per-arm final val +
held-out test CER, promotions vs. noise-driven promotions blocked, and the val→test gap, into a
README here.
