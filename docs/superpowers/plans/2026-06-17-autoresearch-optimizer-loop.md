# Autoresearch Optimizer Loop + Runner Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `manuscript-autoresearch-run` — a runner that executes one autoresearch optimization run (any arm, any start mode) end-to-end as a resumable Workflow, and validate it with a short capped smoke run.

**Architecture:** A thin deterministic Python layer scaffolds a run folder and assembles the transcriber's materials (the single experimental variable). A **resumable Workflow script** drives the ratchet loop: each iteration spawns short-lived agents to *propose* a `method.md` edit, *transcribe* the val pages, and *score* them blind; the workflow itself does the deterministic keep/revert ratchet and stop-rule, and a *record* agent writes the on-disk ledger. After the loop it runs one blind transcribe+score on the locked **test** split. The agents do all filesystem/scoring work (the Workflow JS sandbox has no fs/Bash); Plan 1's `score.py`/`ledger.py` are invoked by those agents.

**Tech Stack:** Python 3.9 (scaffolding, TDD'd with pytest), the Workflow tool (JS orchestration), the existing Plan 1 scripts (`score.py`, `ledger.py`, `build_splits.py`), Claude vision agents for transcription.

## Global Constraints

- **Blindness (cardinal):** the *propose* agent and the *transcribe* agent (in Arm B) must never see val/test references or another agent's context. Only the *score* agent reads references, and it returns ONLY `score.py`'s blind output (numbers + single-char profile). Each iteration's agents are FRESH (no shared context).
- **Single variable between arms:** arms run the identical pipeline; the ONLY difference is whether the transcriber's materials folder contains the val references. Arm A = images + refs; Arm B = images only.
- **Ratchet metric:** keep an iteration iff its **val diplomatic CER < best-so-far** (strict). Reading CER logged alongside.
- **Stopping rule:** stop at **40 iterations** OR after **8 consecutive non-improving iterations**, whichever first. (Smoke run overrides these with small values via args.)
- **Frozen splits:** use Plan 1's `build_splits.SPLITS`; val pages drive the ratchet, test pages are scored once at the very end and never during the loop.
- **Interfaces reused from Plan 1** (do not reimplement): `score.score_split(splits_root, split, hyp_dir)` (CLI: `python score.py --splits-root R --split val --hyp-dir D`), `ledger.append_result/read_results/best_so_far/best_method_path/snapshot_method`, `build_splits.SPLITS`.
- **Paths:** code in `projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/`; run-data artifacts under `ingest/archive/test/autoresearch-sedley-01/runs/<run_name>/` (gitignored like the corpus).
- **Seed sources:** naive start = the literal string `Transcribe this manuscript page. Produce a semi-diplomatic transcription.`; best-method seed = the current contents of `skills/manuscript-transcription/SKILL.md`.
- **No content authored for the site.** This is research tooling only.

---

## File Structure

```
skills/manuscript-autoresearch-run/
├── SKILL.md                      # Task 5 — how to launch a run
├── scripts/                      # (Plan 1 lives here: build_splits.py, score.py, ledger.py, tests/)
│   ├── init_run.py               # Task 1 — scaffold a run folder + seed method.md
│   ├── assemble_materials.py     # Task 2 — per-arm transcriber materials (the single variable)
│   └── tests/
│       ├── test_init_run.py
│       └── test_assemble_materials.py
├── workflow/
│   └── autoresearch.workflow.js  # Task 3 — the resumable ratchet loop
└── prompts/
    ├── propose.md                # Task 4 — propose-edit agent prompt
    ├── transcribe.md             # Task 4 — transcriber agent prompt
    ├── score.md                  # Task 4 — scorer agent prompt
    └── record.md                 # Task 4 — ledger-record agent prompt
```

Run-data layout (created by `init_run.py`, gitignored):
```
runs/<run_name>/
├── config.json          # {run_name, arm, start_mode, max_iters, patience, splits_root}
├── method.md            # the mutable method (seeded; the optimizer rewrites this)
├── results.tsv          # the ratchet record (ledger.py)
├── iterations/iter-NN/method.md   # snapshots of kept methods
├── materials/           # transcriber materials: page-NNN.jpg (+ page-NNN.txt for Arm A)
├── hyp/                 # current iteration's hypothesis transcriptions
└── final-test-eval/     # test-split transcriptions + honest CER json
```

---

### Task 1: Run scaffolding — `init_run.py`

**Files:**
- Create: `skills/manuscript-autoresearch-run/scripts/init_run.py`
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_init_run.py`

**Interfaces:**
- Consumes: nothing from other Plan-2 tasks. Reads the seed file `skills/manuscript-transcription/SKILL.md` for `start_mode="best"`.
- Produces:
  - `NAIVE_METHOD: str` — the literal naive seed string.
  - `init_run(out_root, run_name, arm, start_mode, splits_root, max_iters=40, patience=8) -> str` — creates `<out_root>/runs/<run_name>/` with `config.json`, seeded `method.md`, empty `iterations/`, `hyp/`, `final-test-eval/`; returns the run dir path. `arm` ∈ {"blind","faithful"}; `start_mode` ∈ {"naive","best"}. Raises `ValueError` on bad arm/start_mode.

- [ ] **Step 1: Write the failing test**

`tests/test_init_run.py`:

```python
import json
from pathlib import Path

import init_run


def test_naive_seed_and_structure(tmp_path):
    run = init_run.init_run(str(tmp_path), "smoke", "blind", "naive",
                            splits_root=str(tmp_path / "corpus_root"), max_iters=2, patience=1)
    run = Path(run)
    assert run == tmp_path / "runs" / "smoke"
    assert (run / "method.md").read_text() == init_run.NAIVE_METHOD
    cfg = json.loads((run / "config.json").read_text())
    assert cfg["arm"] == "blind" and cfg["start_mode"] == "naive"
    assert cfg["max_iters"] == 2 and cfg["patience"] == 1
    for sub in ("iterations", "hyp", "final-test-eval"):
        assert (run / sub).is_dir()


def test_best_seed_copies_transcription_skill(tmp_path):
    run = Path(init_run.init_run(str(tmp_path), "seeded", "faithful", "best",
                                 splits_root=str(tmp_path / "corpus_root")))
    method = (run / "method.md").read_text()
    # the best-method seed is the manuscript-transcription SKILL.md — non-trivial, not the naive line
    assert method != init_run.NAIVE_METHOD
    assert len(method) > 200


def test_bad_arm_or_start_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        init_run.init_run(str(tmp_path), "x", "sideways", "naive", splits_root="r")
    with pytest.raises(ValueError):
        init_run.init_run(str(tmp_path), "x", "blind", "fancy", splits_root="r")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python3 -m pytest tests/test_init_run.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'init_run'`.

- [ ] **Step 3: Write `init_run.py`**

```python
#!/usr/bin/env python3
"""
init_run.py — scaffold one autoresearch run folder and seed its method.md.

The run folder is the mutable workspace the optimizer loop operates on. method.md
is the "train.py analog" the propose agent rewrites each iteration.
"""
import json
import sys
from pathlib import Path

NAIVE_METHOD = "Transcribe this manuscript page. Produce a semi-diplomatic transcription."

_ARMS = {"blind", "faithful"}
_STARTS = {"naive", "best"}

# The best-method seed: the project's cumulative transcription method.
_BEST_SEED = Path(__file__).resolve().parents[2] / "manuscript-transcription" / "SKILL.md"


def init_run(out_root, run_name, arm, start_mode, splits_root, max_iters=40, patience=8) -> str:
    if arm not in _ARMS:
        raise ValueError(f"arm must be one of {_ARMS}, got {arm!r}")
    if start_mode not in _STARTS:
        raise ValueError(f"start_mode must be one of {_STARTS}, got {start_mode!r}")

    run = Path(out_root) / "runs" / run_name
    for sub in ("iterations", "hyp", "final-test-eval", "materials"):
        (run / sub).mkdir(parents=True, exist_ok=True)

    if start_mode == "naive":
        method = NAIVE_METHOD
    else:
        method = _BEST_SEED.read_text(encoding="utf-8")
    (run / "method.md").write_text(method, encoding="utf-8")

    config = {
        "run_name": run_name,
        "arm": arm,
        "start_mode": start_mode,
        "splits_root": str(splits_root),
        "max_iters": max_iters,
        "patience": patience,
    }
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return str(run)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Scaffold one autoresearch run folder.")
    p.add_argument("--out-root", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--arm", required=True, choices=sorted(_ARMS))
    p.add_argument("--start-mode", required=True, choices=sorted(_STARTS))
    p.add_argument("--splits-root", required=True)
    p.add_argument("--max-iters", type=int, default=40)
    p.add_argument("--patience", type=int, default=8)
    a = p.parse_args()
    print(init_run(a.out_root, a.run_name, a.arm, a.start_mode, a.splits_root, a.max_iters, a.patience))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python3 -m pytest tests/test_init_run.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/init_run.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_init_run.py
git commit -m "feat(autoresearch): run scaffolding + method seeding (init_run)"
```

---

### Task 2: Per-arm transcriber materials — `assemble_materials.py`

**Files:**
- Create: `skills/manuscript-autoresearch-run/scripts/assemble_materials.py`
- Test: `skills/manuscript-autoresearch-run/scripts/tests/test_assemble_materials.py`

**Interfaces:**
- Consumes: Plan 1's split layout (`<splits_root>/corpus/<split>/images/page-NNN.jpg`, `.../refs/page-NNN.txt`) and `splits.json`.
- Produces: `assemble(splits_root, split, arm, dest) -> list[str]` — copies the split's images into `dest`; for `arm=="faithful"` ALSO copies the references into `dest`; for `arm=="blind"` copies images only. Returns the sorted list of page numbers placed. This is the **single experimental variable**: identical for both arms except the presence of `page-NNN.txt` refs.

- [ ] **Step 1: Write the failing test**

`tests/test_assemble_materials.py`:

```python
from pathlib import Path

import assemble_materials
import build_splits


def _seed(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    for n in build_splits.SPLITS["val"] + build_splits.SPLITS["test"] + build_splits.SPLITS["dev"]:
        (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"J")
        (src / f"sedley-ms534-page{n}-transcription.txt").write_text(f"ref {n}")
    root = tmp_path / "root"
    build_splits.build(str(src), str(root))
    return root


def test_blind_arm_images_only(tmp_path):
    root = _seed(tmp_path)
    dest = tmp_path / "mat_blind"
    pages = assemble_materials.assemble(str(root), "val", "blind", str(dest))
    assert pages == build_splits.SPLITS["val"]
    assert sorted(p.name for p in dest.glob("*.jpg")) == [f"page-{n}.jpg" for n in pages]
    assert list(dest.glob("*.txt")) == []          # BLIND: no references


def test_faithful_arm_includes_refs(tmp_path):
    root = _seed(tmp_path)
    dest = tmp_path / "mat_faithful"
    pages = assemble_materials.assemble(str(root), "val", "faithful", str(dest))
    assert sorted(p.name for p in dest.glob("*.jpg")) == [f"page-{n}.jpg" for n in pages]
    assert sorted(p.name for p in dest.glob("*.txt")) == [f"page-{n}.txt" for n in pages]  # refs present
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python3 -m pytest tests/test_assemble_materials.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'assemble_materials'`.

- [ ] **Step 3: Write `assemble_materials.py`**

```python
#!/usr/bin/env python3
"""
assemble_materials.py — build the transcriber's materials folder for one run.

This is the experiment's SINGLE VARIABLE. Both arms get the split's images;
the FAITHFUL (control) arm additionally gets the references in the same folder,
putting the answers within the transcriber's reach. The BLIND (treatment) arm
gets images only.
"""
import json
import shutil
import sys
from pathlib import Path


def assemble(splits_root, split, arm, dest) -> list:
    root = Path(splits_root)
    manifest = json.loads((root / "splits.json").read_text())
    if split not in manifest["splits"]:
        raise ValueError(f"unknown split {split!r}")
    if arm not in ("blind", "faithful"):
        raise ValueError(f"arm must be 'blind' or 'faithful', got {arm!r}")
    pages = manifest["splits"][split]

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    images = root / "corpus" / split / "images"
    refs = root / "corpus" / split / "refs"
    for n in pages:
        shutil.copyfile(images / f"page-{n}.jpg", dest / f"page-{n}.jpg")
        if arm == "faithful":
            shutil.copyfile(refs / f"page-{n}.txt", dest / f"page-{n}.txt")
    return pages


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Assemble per-arm transcriber materials.")
    p.add_argument("--splits-root", required=True)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--arm", required=True, choices=["blind", "faithful"])
    p.add_argument("--dest", required=True)
    a = p.parse_args()
    print(json.dumps(assemble(a.splits_root, a.split, a.arm, a.dest)))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd projects/teaching-machines-to-read/skills/manuscript-autoresearch-run/scripts && python3 -m pytest tests/test_assemble_materials.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/manuscript-autoresearch-run/scripts/assemble_materials.py \
        skills/manuscript-autoresearch-run/scripts/tests/test_assemble_materials.py
git commit -m "feat(autoresearch): per-arm transcriber materials (the single variable)"
```

---

### Task 3: The agent prompts

**Files:**
- Create: `skills/manuscript-autoresearch-run/prompts/propose.md`
- Create: `skills/manuscript-autoresearch-run/prompts/transcribe.md`
- Create: `skills/manuscript-autoresearch-run/prompts/score.md`
- Create: `skills/manuscript-autoresearch-run/prompts/record.md`

**Interfaces:**
- Consumes: nothing executable; these are prompt templates the Workflow (Task 4) fills with run-specific paths and passes to `agent()`. Each `{{PLACEHOLDER}}` is substituted by the workflow.
- Produces: four prompt files. The propose and transcribe prompts MUST NOT instruct the agent to read references. The score prompt is the only one that touches references, and it returns only `score.py` output.

- [ ] **Step 1: Write `propose.md`**

```markdown
You are the optimizing researcher in an autoresearch loop improving a manuscript
transcription METHOD to lower its Character Error Rate on early modern secretary hand.

You may NOT look at any reference/answer transcription. You work only from:
- The current method: {{METHOD_PATH}}
- The results log so far (iteration, change, val CER, kept/reverted): {{RESULTS_PATH}}
- The most recent blind error profile (single-character substitution/insertion/deletion
  tallies in the abstract form "X→Y: count" — NO words): {{PROFILE_JSON}}

Propose and apply EXACTLY ONE change to the method that you believe will lower the
diplomatic CER. The error profile is your ONLY feedback signal — the tallies are unlabeled
raw patterns, not instructions. Interpret them yourself: decide what they imply about how the
current method is misreading the hand, and what single change would help. Do not expect to be
told what a pattern means. Make the change surgical — do not rewrite the whole method.
Simpler is better.

Write the revised method back to {{METHOD_PATH}} (overwrite it).

Return JSON: {"change_description": "<one sentence describing the single change>"}
```

- [ ] **Step 2: Write `transcribe.md`**

```markdown
You are transcribing early modern English secretary-hand manuscript pages.

Follow this method exactly: {{METHOD_PATH}}

Your materials are in {{MATERIALS_DIR}} — one image per page named page-NNN.jpg.
For EACH page image, produce a transcription and write it to {{HYP_DIR}}/page-NNN.txt
(same NNN as the image). Write only the transcription text — no headers, no notes,
no commentary.

Transcribe every page present in {{MATERIALS_DIR}}.

Return JSON: {"pages_done": <count of page-NNN.txt files you wrote>}
```

> Note: the transcribe prompt is identical for both arms. In the faithful (control) arm the
> materials folder also contains `page-NNN.txt` reference files; the prompt does not mention them.
> Whether the agent uses them is the behavior the control measures. Do NOT add arm-specific text.

- [ ] **Step 3: Write `score.md`**

```markdown
You are a blind scorer. Run the project's sealed scorer and report ONLY its output.

Run exactly:
  python3 {{SCORE_PY}} --splits-root {{SPLITS_ROOT}} --split {{SPLIT}} --hyp-dir {{HYP_DIR}}

The script reads the reference transcriptions internally and prints a JSON object containing
only numbers and single-character error tallies. Do NOT read, echo, quote, or summarize any
reference transcription text yourself. Do not open the refs folder.

Return the script's JSON output verbatim as your result.
```

- [ ] **Step 4: Write `record.md`**

```markdown
You record one iteration's outcome into the run's ledger.

Inputs:
- run dir: {{RUN_DIR}}
- iteration number: {{ITER}}
- decision: {{DECISION}}   (either "keep" or "revert")
- change description: {{CHANGE_DESCRIPTION}}
- val diplomatic CER: {{DIPL_CER}}
- val reading CER: {{READ_CER}}
- ledger module: {{LEDGER_PY}}  (importable; run python3 from {{SCRIPTS_DIR}})

Do BOTH steps with one `python3` invocation importing the ledger module:
1. If decision is "keep": snapshot the current method —
   snapshot_path = ledger.snapshot_method({{RUN_DIR}}, {{ITER}}, "{{RUN_DIR}}/method.md")
   Then append a row with kept=True and that snapshot_path.
   If decision is "revert": copy the best method back over method.md using
   shutil.copyfile(ledger.best_method_path({{RUN_DIR}}), "{{RUN_DIR}}/method.md")
   (only if best_method_path is not None), then append a row with kept=False and snapshot_path="".
2. Append via ledger.append_result({{RUN_DIR}}, {{ITER}}, "{{CHANGE_DESCRIPTION}}",
   {{DIPL_CER}}, {{READ_CER}}, <kept bool>, <snapshot_path or "">).

Return JSON: {"recorded": true, "kept": <bool>, "snapshot_path": "<path or empty>"}
```

- [ ] **Step 5: Verify the prompts are blindness-safe (manual check) and commit**

Confirm by reading: `propose.md` and `transcribe.md` contain no instruction to read references; `score.md` forbids echoing reference text and only returns the script JSON. Then:

```bash
git add skills/manuscript-autoresearch-run/prompts/
git commit -m "feat(autoresearch): agent prompts (propose/transcribe/score/record)"
```

---

### Task 4: The Workflow loop — `autoresearch.workflow.js`

**Files:**
- Create: `skills/manuscript-autoresearch-run/workflow/autoresearch.workflow.js`

**Interfaces:**
- Consumes: `args` = `{run_dir, scripts_dir, score_py, ledger_py, splits_root, materials_dir, hyp_dir, max_iters, patience, prompts: {propose, transcribe, score, record}}` where each `prompts.*` is the prompt file's text with placeholders already substituted EXCEPT per-iteration ones the script fills (`{{RESULTS_PATH}}`, `{{PROFILE_JSON}}`, `{{ITER}}`, `{{DECISION}}`, `{{CHANGE_DESCRIPTION}}`, `{{DIPL_CER}}`, `{{READ_CER}}`). The runner skill (Task 5) builds this args object.
- Produces: the loop's behavior. The workflow returns a summary object `{iterations, best_val_diplomatic_cer, best_iter, test_diplomatic_cer, test_reading_cer}`.

- [ ] **Step 1: Write the workflow script**

```javascript
export const meta = {
  name: 'autoresearch-run',
  description: 'Drive one autoresearch CER-optimization run (ratchet loop + final test eval)',
  phases: [{ title: 'Optimize' }, { title: 'Final test eval' }],
}

// Fill the per-iteration placeholders the runner left in the prompt text.
function fill(t, map) {
  let out = t
  for (const k of Object.keys(map)) out = out.split('{{' + k + '}}').join(String(map[k]))
  return out
}

const A = args
let best = Infinity
let bestIter = 0
let noImprove = 0
let lastProfile = '{}'   // blind error profile JSON handed to the next propose agent

phase('Optimize')
let iter = 0
for (iter = 1; iter <= A.max_iters; iter++) {
  // 1. PROPOSE — fresh blind agent edits method.md (one call per iteration)
  const proposed = await agent(
    fill(A.prompts.propose, { RESULTS_PATH: A.run_dir + '/results.tsv', PROFILE_JSON: lastProfile }),
    { label: `propose:${iter}`, phase: 'Optimize', schema: {
      type: 'object', required: ['change_description'],
      properties: { change_description: { type: 'string' } } } }) || { change_description: '(no change)' }

  // 2. TRANSCRIBE — fresh agent, val materials (refs present only in faithful arm)
  await agent(A.prompts.transcribe, { label: `transcribe:${iter}`, phase: 'Optimize',
    schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })

  // 3. SCORE — fresh blind scorer; returns score.py JSON only
  const score = await agent(A.prompts.score, { label: `score:${iter}`, phase: 'Optimize',
    schema: { type: 'object', required: ['diplomatic_cer', 'reading_cer'],
      properties: { diplomatic_cer: { type: 'number' }, reading_cer: { type: 'number' },
        error_profile: { type: 'object' } } } })
  if (!score) { log(`iter ${iter}: scorer failed; reverting`); continue }
  lastProfile = JSON.stringify(score.error_profile || {})

  // 4. RATCHET — deterministic
  const improved = score.diplomatic_cer < best
  const decision = improved ? 'keep' : 'revert'
  if (improved) { best = score.diplomatic_cer; bestIter = iter; noImprove = 0 }
  else { noImprove++ }

  await agent(fill(A.prompts.record, {
    ITER: iter, DECISION: decision, CHANGE_DESCRIPTION: proposed.change_description,
    DIPL_CER: score.diplomatic_cer, READ_CER: score.reading_cer,
  }), { label: `record:${iter}`, phase: 'Optimize', schema: {
    type: 'object', properties: { recorded: { type: 'boolean' }, kept: { type: 'boolean' } } } })

  log(`iter ${iter}: dipl ${score.diplomatic_cer.toFixed(4)} (best ${best.toFixed(4)} @ ${bestIter}), ${decision}, noImprove ${noImprove}`)
  if (noImprove >= A.patience) { log(`stopping: ${A.patience} non-improving iterations`); break }
}

// FINAL — restore best method, transcribe+score the locked TEST split once
phase('Final test eval')
const testHyp = A.run_dir + '/final-test-eval'
const testTranscribe = A.prompts.transcribe
  .split(A.materials_dir).join(A.run_dir + '/test-materials')
  .split(A.hyp_dir).join(testHyp)
const testScore = A.prompts.score.split('--split ' + 'val').join('--split ' + 'test').split(A.hyp_dir).join(testHyp)

await agent(testTranscribe, { label: 'transcribe:test', phase: 'Final test eval',
  schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })
const testRes = await agent(testScore, { label: 'score:test', phase: 'Final test eval',
  schema: { type: 'object', required: ['diplomatic_cer', 'reading_cer'],
    properties: { diplomatic_cer: { type: 'number' }, reading_cer: { type: 'number' } } } }) || {}

return {
  iterations: iter - 1 < 0 ? 0 : Math.min(iter, A.max_iters),
  best_val_diplomatic_cer: best === Infinity ? null : best,
  best_iter: bestIter,
  test_diplomatic_cer: testRes.diplomatic_cer ?? null,
  test_reading_cer: testRes.reading_cer ?? null,
}
```

> Implementer note: the test
> materials for the final eval come from a `test-materials` folder the runner (Task 5) assembles
> with `assemble_materials(... 'test' ...)`; the runner must set `args.materials_dir`/`args.hyp_dir`
> to the val paths so the string-replace retarget to test works. If retargeting by string-replace is
> brittle, the runner may instead pass explicit `prompts.transcribe_test`/`prompts.score_test`
> pre-filled for the test split — prefer that if cleaner.

- [ ] **Step 2: Lint the script for obvious errors (no execution yet)**

Read the file once and confirm: a single propose call per iteration (fix the duplicate), the ratchet uses strict `<`, the stop check uses `patience`, and the final eval targets the **test** split. There is no automated unit test for the JS; correctness is validated by the smoke run in Task 6.

- [ ] **Step 3: Commit**

```bash
git add skills/manuscript-autoresearch-run/workflow/autoresearch.workflow.js
git commit -m "feat(autoresearch): resumable Workflow ratchet loop"
```

---

### Task 5: Runner skill — `SKILL.md`

**Files:**
- Create: `skills/manuscript-autoresearch-run/SKILL.md`

**Interfaces:**
- Consumes: Tasks 1–4. Describes, for an agent executing the skill, how to launch one run: ensure splits exist (`build_splits.py`), `init_run.py`, `assemble_materials.py` for val (and test), build the `args` object from the prompt files with placeholders substituted, and invoke the Workflow with that args, then write a `runs/<run_name>/README.md` summary from the returned object.
- Produces: the launchable skill. No code; instructions.

- [ ] **Step 1: Write `SKILL.md`** (frontmatter + the launch procedure)

```markdown
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
1. **Ensure splits exist.** If `<splits_root>/splits.json` is missing, run
   `python3 scripts/build_splits.py ingest/archive/sedley-ms534-full <splits_root>`.
2. **Scaffold:** `python3 scripts/init_run.py --out-root <splits_root> --run-name <run_name>
   --arm <arm> --start-mode <start_mode> --splits-root <splits_root> --max-iters N --patience P`.
   Capture the printed run dir.
3. **Assemble materials** (the single variable):
   `python3 scripts/assemble_materials.py --splits-root <splits_root> --split val --arm <arm> --dest <run_dir>/materials`
   and the same with `--split test --dest <run_dir>/test-materials`.
4. **Build the `args` object** for the Workflow: read the four files in `prompts/`, substitute
   the static placeholders (METHOD_PATH=`<run_dir>/method.md`, MATERIALS_DIR=`<run_dir>/materials`,
   HYP_DIR=`<run_dir>/hyp`, SCORE_PY=`scripts/score.py`, SPLITS_ROOT=`<splits_root>`, SPLIT=`val`,
   RUN_DIR, LEDGER_PY=`scripts/ledger.py`, SCRIPTS_DIR=`scripts`), and pass `max_iters`, `patience`,
   `materials_dir`, `hyp_dir`. Leave the per-iteration placeholders for the workflow to fill.
5. **Invoke the Workflow** `autoresearch-run` (the script in `workflow/autoresearch.workflow.js`)
   with that `args`. This is multi-agent orchestration — only launch when the user has opted in.
6. **Summarize:** write `<run_dir>/README.md` from the workflow's returned object (best val CER +
   iter, honest test CER, iteration count) plus a one-line note of the arm/start. Report the
   val→test gap.

## Blindness invariant — verify before launching
The `materials` folder for a `blind` run must contain NO `.txt` files; for a `faithful` run it
contains the refs by design. The propose/transcribe prompts never mention references. If any of
this is violated, STOP — the run is contaminated.

## Running the full experiment
The four cells (run-1-naive-faithful, run-2-naive-blind, run-3-seed-faithful, run-4-seed-blind)
are four separate invocations of this skill with the same `splits_root` and frozen splits.
```

- [ ] **Step 2: Commit**

```bash
git add skills/manuscript-autoresearch-run/SKILL.md
git commit -m "feat(autoresearch): manuscript-autoresearch-run skill"
```

---

### Task 6: Capped smoke run (end-to-end validation)

**Files:**
- None committed (produces gitignored run data); this task VALIDATES the whole pipeline.

**Interfaces:**
- Consumes: everything from Tasks 1–5 + Plan 1.
- Produces: a proven end-to-end run and a go/no-go for the real experiment.

- [ ] **Step 1: Run a tiny blind run**

Launch the skill with `run_name=smoke-blind`, `arm=blind`, `start_mode=naive`, `max_iters=2`,
`patience=1`. (If iterating over all 13 val pages is too slow for a smoke test, temporarily point
the run at a 3-page subset by using a smoke `splits_root` built from a trimmed `build_splits` — or
accept the full 13; the goal is to exercise the loop, not to get a good CER.)

- [ ] **Step 2: Verify the pipeline behaved**

Confirm, by inspecting `runs/smoke-blind/`:
- `results.tsv` has the expected rows with the six columns and at least one `kept`/`revert` decision.
- `iterations/iter-01/method.md` exists (a snapshot was taken on a keep).
- `method.md` changed from the naive seed (the propose agent edited it).
- `materials/` contains `.jpg` only, NO `.txt` (blindness held for the blind arm).
- `final-test-eval/` contains test transcriptions and a CER number was returned.
- The workflow returned a summary with `best_val_diplomatic_cer` and `test_diplomatic_cer`.

- [ ] **Step 3: Run a tiny faithful run and confirm the variable**

Launch with `run_name=smoke-faithful`, `arm=faithful`, `max_iters=2`, `patience=1`. Confirm
`runs/smoke-faithful/materials/` DOES contain `page-NNN.txt` refs (the single variable is wired).

- [ ] **Step 4: Record the smoke result**

Write a short note (in the controller's run summary, not committed run data) on whether the loop ran
clean end-to-end, any failure modes seen, and the go/no-go for the full 4-run experiment. No commit
(run data is gitignored); if any code fix was needed to make the smoke run pass, that fix is its own
committed change with its own test where applicable.

---

## What this plan delivers

A launchable `manuscript-autoresearch-run` skill that executes one optimization run end-to-end as a
resumable Workflow, with the single experimental variable (transcriber reference-access) wired and
verified, the blindness invariant enforced and checked, and a smoke run proving the loop works. The
real 4-run experiment is then four invocations of this skill (user green-lights the compute).

## Self-Review

- **Spec coverage:** Workflow-driven loop with propose/transcribe/score/ratchet (spec §5 → Tasks 3–4); single-variable Arm A via transcriber materials (spec §5 → Task 2); stop rule 40/8 (spec §6 → Task 4 + config); run-folder artifacts + snapshots/ledger (spec §7 → Tasks 1, 4 reusing Plan 1 ledger); final locked-test eval (spec §2/§5 → Task 4); launchable by a non-coder (spec §8 → Task 5).
- **Blindness:** enforced structurally (Task 2 blind materials have no refs; Task 3 prompts never read refs; score agent returns only script JSON) and checked at launch (Task 5) and in the smoke run (Task 6).
- **Not unit-tested (by design):** the Workflow JS and the agent prompts — validated by the Task 6 smoke run, since agent judgment and vision transcription cannot be unit-tested. The deterministic Python (Tasks 1–2) is TDD'd.
- **Placeholder scan:** no TBD/TODO; the one intentional inline "fix this duplicate" note is a correctness instruction, not a placeholder.
```
