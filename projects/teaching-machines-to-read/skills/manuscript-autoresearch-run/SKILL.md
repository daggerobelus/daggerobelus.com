---
name: manuscript-autoresearch-run
description: >
  Run one autoresearch CER-optimization run on a manuscript: an agent loop that
  ratchets a transcription method to lower its blind Character Error Rate. Use when
  asked to run an autoresearch optimization, an autoresearch arm, or the Sedley
  optimization experiment. Drives the resumable Workflow loop end to end.
---

# Manuscript Autoresearch Run

Launch ONE optimization run. A run = pick an **arm** (`blind` or `faithful`) and a
**start mode** (`naive` or `best`); the loop then proposes method edits, transcribes the
val pages, scores them blind, and keeps edits that lower diplomatic CER — until the stop
rule. Then it scores the locked **test** split once for the honest number.

## Inputs you need
- `run_name` (e.g. `run-2-naive-blind`), `arm`, `start_mode`, `splits_root`
  (the Plan-1 split root, default `ingest/archive/test/autoresearch-sedley-01`),
  and optional `max_iters` / `patience` (defaults 40 / 8; use small values for a smoke run).

## Procedure

### 1. Ensure splits exist
If `<splits_root>/splits.json` is missing, run:
```
python3 scripts/build_splits.py ingest/archive/sedley-ms534-full <splits_root>
```

### 2. Scaffold the run
```
python3 scripts/init_run.py \
  --out-root <splits_root> \
  --run-name <run_name> \
  --arm <arm> \
  --start-mode <start_mode> \
  --splits-root <splits_root> \
  --max-iters <N> \
  --patience <P>
```
Capture the printed run dir path (referred to as `<run_dir>` below).

### 3. Assemble materials
Assemble both val and test materials — the val set is the optimization target; test is
the held-out honest set used once at the very end.

**Val materials** (the single variable for the loop):
```
python3 scripts/assemble_materials.py \
  --splits-root <splits_root> \
  --split val \
  --arm <arm> \
  --dest <run_dir>/materials
```

**Test materials** (held-out; assembled now, used only after the loop stops):
```
python3 scripts/assemble_materials.py \
  --splits-root <splits_root> \
  --split test \
  --arm <arm> \
  --dest <run_dir>/test-materials
```

### 4. Blindness invariant — verify before launching
**For a `blind` arm run:** `<run_dir>/materials/` and `<run_dir>/test-materials/` must
contain NO `.txt` reference files — images only. Check before proceeding:
```
ls <run_dir>/materials/*.txt   # should return "no matches"
ls <run_dir>/test-materials/*.txt  # should return "no matches"
```
The propose/transcribe prompts must never mention references.

**For a `faithful` arm run:** `.txt` reference files are present by design; that is expected.

If the blindness invariant is violated, STOP — the run is contaminated and results cannot
be reported.

### 5. Build the filled prompt files and the `args` object for the Workflow
Read the four template files in `prompts/` (`propose.md`, `transcribe.md`, `score.md`,
`record.md`) and substitute the static placeholders listed below. Leave the **per-iteration**
placeholders intact — the Workflow injects those at runtime: `{{PROFILE_JSON}}` (in propose)
and `{{ITER}}`, `{{DECISION}}`, `{{CHANGE_DESCRIPTION}}`, `{{DIPL_CER}}`, `{{READ_CER}}` (in
record).

**Write each filled prompt to a file** under `<run_dir>/prompts/` (e.g.
`<run_dir>/prompts/propose.md`, `…/transcribe.md`, `…/score.md`, `…/record.md`,
`…/transcribe_test.md`, `…/score_test.md`). The Workflow is passed the prompt **file paths**,
not the prompt text — this keeps `args` tiny regardless of prompt size, and each agent reads
its instructions from the file.

**Static placeholder substitutions for the val-facing prompts:**

| Placeholder | Value |
|---|---|
| `{{METHOD_PATH}}` | `<run_dir>/method.md` |
| `{{RESULTS_PATH}}` | `<run_dir>/results.tsv` |
| `{{MATERIALS_DIR}}` | `<run_dir>/materials` |
| `{{HYP_DIR}}` | `<run_dir>/hyp` |
| `{{SCORE_PY}}` | `scripts/score.py` (absolute path) |
| `{{SPLITS_ROOT}}` | `<splits_root>` |
| `{{SPLIT}}` | `val` |
| `{{RUN_DIR}}` | `<run_dir>` |
| `{{LEDGER_PY}}` | `scripts/ledger.py` (absolute path) |
| `{{SCRIPTS_DIR}}` | `scripts` (absolute path) |

**Also build the two test-split prompts** by filling `transcribe.md` and `score.md` with
the TEST-specific values:

| Placeholder | Value for test prompts |
|---|---|
| `{{METHOD_PATH}}` | `<run_dir>/method.md` |
| `{{MATERIALS_DIR}}` | `<run_dir>/test-materials` |
| `{{HYP_DIR}}` | `<run_dir>/final-test-eval` |
| `{{SCORE_PY}}` | `scripts/score.py` |
| `{{SPLITS_ROOT}}` | `<splits_root>` |
| `{{SPLIT}}` | `test` |

Assemble the `args` object (prompt values are FILE PATHS to the filled files written above):
```js
{
  run_dir:      '<run_dir>',
  max_iters:    <N>,
  patience:     <P>,
  prompts: {
    propose:          '<run_dir>/prompts/propose.md',          // val, RESULTS_PATH filled, {{PROFILE_JSON}} left
    transcribe:       '<run_dir>/prompts/transcribe.md',       // val
    score:            '<run_dir>/prompts/score.md',            // val
    record:           '<run_dir>/prompts/record.md',           // {{ITER}}/{{DECISION}}/… left
    transcribe_test:  '<run_dir>/prompts/transcribe_test.md',  // test materials + final-test-eval
    score_test:       '<run_dir>/prompts/score_test.md',       // SPLIT=test
  }
}
```

### 6. Invoke the Workflow
This is multi-agent orchestration that will spawn many sub-agents over potentially many
iterations. **Only launch when the user has explicitly opted in** to running a full
optimization experiment.

Invoke the `autoresearch-run` Workflow (`workflow/autoresearch.workflow.js`) with the
`args` object built above. **Pass `args` as an actual JSON object, not a stringified one**
(the workflow defensively `JSON.parse`s a string, but passing an object is correct).

> **Note on method state before the final test eval:** The ratchet loop relies on
> `method.md` being at the best-kept state at all times — the record agent restores best on
> every revert. Before the final test eval phase runs, sanity-check that
> `iterations/iter-<best_iter>/method.md` matches `<run_dir>/method.md` (e.g. compare
> their SHA or diff them). If they differ, restore from the snapshot before proceeding.

### 7. Summarize
Write `<run_dir>/README.md` from the Workflow's returned object. Include:
- Arm and start mode
- Total iterations run
- Best val diplomatic CER + which iteration achieved it
- Honest test diplomatic CER and reading CER
- Val→test gap (test CER − val best CER; a large positive gap may indicate overfitting to val)
- One-line note of any anomalies (e.g. early stop, scorer failures)

Report the val→test gap in your reply to the user.

## Running the full experiment
The four cells (run-1-naive-faithful, run-2-naive-blind, run-3-seed-faithful, run-4-seed-blind)
are four separate invocations of this skill with the same `splits_root` and frozen splits.
Run them sequentially (or in parallel if compute allows), then compare their honest test CERs.
