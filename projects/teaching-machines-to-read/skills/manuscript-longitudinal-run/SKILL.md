---
name: manuscript-longitudinal-run
description: >
  Run a within-hand longitudinal transcription experiment — one scribal hand
  worked through in ordered SETS by a single continuous learner, with relay
  recovery if it drops, and per-cycle blind CER. Use this skill when running a
  whole manuscript (or a long single-hand stretch) through the cumulative method:
  one agent learns the hand start to finish in one context; if it drops or stalls,
  a fresh agent resumes from the latest snapshot (a logged "seam"). Use this (not
  manuscript-test-run, which is single-page parallel) whenever the task is a
  multi-set, single-hand run with snapshots, rolling revision, and a learning
  trajectory. Triggers: "full run," "run the whole manuscript," "longitudinal
  run," "single continuous learner."
---

# Manuscript Longitudinal Run — Per-Set Relay

Orchestrate a within-hand longitudinal run: one hand, processed in ordered sets of ~5 pages, with the cumulative method. See `within-hand-longitudinal-design.md` for the experiment's rationale.

**This is the single entry point for a full run — it drives the other skills automatically.** Invoke only this skill. It inlines `manuscript-transcription` into each learner's prompt (so the learner reads the hand by that method), and it launches blind evaluators that follow `manuscript-evaluation` (which cleans references and reports diplomatic + reading CER). You do not invoke those two yourself; this runner cascades to them.

**Run mode — single continuous learner, with relay recovery.** The PRIMARY model is **one continuous agent** that works the whole hand in a single context — one mind learning the scribe start to finish (the faithful "single learner," the human-student analog). The relay is a **safety net, not the default**: long runs (a full ~39-page hand) are drop-prone, and in this environment a dropped agent cannot be resumed with its memory intact, so if the continuous agent fails partway, a *fresh* agent picks up from the latest snapshot and finishes. A clean run is one mind; a recovered run has a **seam** where the relay took over. Tag which is which (below) — clean runs are the pure single-learner data. The snapshot-preservation is what makes recovery possible: the dropped agent's externalized notes are the handoff.

This is rigorous research: isolation, blind evaluation, and full preservation are not optional. The shared principles (folder isolation, integrity audit, JSON-records-everything) are the same as `manuscript-test-run` — read it for those; this skill covers only what's different about the relay.

## Inputs (confirm before starting)

1. **Manuscript** — ordered page images for ONE hand, and the page-aligned references. Identify and EXCLUDE non-hand pages (flyleaf, blank, later inscriptions) up front; the run is one scribe.
2. **Set size** — default 5 pages (the project's "sweet spot").
3. **Number of learners (N)** — independent relay chains, for spread. Default 5 for a first data point; scale up once stable.
4. **Transcription skill** — `skills/manuscript-transcription/SKILL.md`.

## Layout

Run under `/tmp/manuscript-runs/<run-id>/` (outside the project — isolation + pre-approved sandbox). References stay in the PROJECT (never under the run dir, so learners can't reach them).

```
/tmp/manuscript-runs/<run-id>/
├── learner-1/
│   ├── images/pageNNN.jpg        # all of the hand's pages, in order
│   ├── paleography-guide.md      # copy
│   ├── vocab-reference.txt       # copy
│   ├── set-NN/pageNNN-forward.txt, pageNNN-notes.txt
│   ├── alphabet-after-set-NN.txt # numbered snapshots, never overwritten
│   ├── revisions/...             # rolling revision versions + revision-log.md
│   └── final/pageNNN.txt
├── learner-2..N/ (same)
└── eval/                         # eval outputs — NOT readable by learners mid-run
```

## Run the learner (single continuous agent)

**Default: one continuous agent per learner**, working the whole hand in one context — all sets in order, building and reusing its alphabet in its own context and notes as it goes. This is the faithful single-learner model. Different learners (for spread) are separate single agents, run **in parallel**.

Its prompt inlines: the transcription skill (full text) and the paleography guide (full text). The page images are file paths in order (`images/pageNNN.jpg`); the vocab reference is a file path (too large to inline). It is told the set boundaries and to run the full per-hand cycle (forward → numbered snapshot → rolling revision) set by set, writing **every artifact to disk as it goes** — both because preservation is required and because those files are the recovery handoff.

**Blindness (critical):** the agent sees its images + its own notes only. It NEVER sees the reference, and per-cycle CER is **never fed back** to it mid-run — that would let it learn from the answer key. Evaluation is out-of-band (below).

## Relay recovery (only on drop/stall)

If the continuous agent drops (socket error) or stalls (watchdog) before finishing:
1. Inspect its folder — the latest snapshot and completed forward/revision files are preserved.
2. Launch a **fresh agent** that reads the latest snapshot (inlined) + the still-open flag list + which pages are already done, and **continues from the first incomplete unit** (finish the in-progress set, then the remaining sets, same cycle).
3. If it drops again, repeat. Each recovery is a relay hop.

This guarantees completion. The cost: from the drop point on, the run is note-passing (a fresh mind reading notes), not one continuous mind — a **seam**.

**Record the seam(s).** For each learner, log whether it completed in one context (**clean**) or needed relay recovery, and at which set(s) the seam(s) fell. Clean runs are the pure single-learner data; recovered runs are usable but caveated. This distinction matters for analysis — when reading the within-hand learning curve, separate clean one-mind runs from relay-recovered ones. Never silently paper over a drop.

## Evaluation (out-of-band, blind, with cleaning)

After a learner's chain finishes (the run does not depend on live CER), launch **blind evaluation agents** following `manuscript-evaluation/SKILL.md` — which now cleans references (Step 2) and reports **both diplomatic and reading CER** (Step 3). Compute, per learner:
- **Per-set forward CER** — each set's `pageNNN-forward.txt` vs reference. Does the agent read NEW pages better as the snapshot matures?
- **Post-revision CER per round** — after set N's revision, the current version (latest revision else forward) of every page so far. Does revisiting old flags with maturer notes help?
- **Overall (all pages, latest versions)** — diplomatic and reading.

Evaluators see transcription text + reference only — never the images, never the snapshots-as-answer (they get the hypothesis text, not the carried state). Keep eval outputs in `eval/`, outside any learner folder.

## Preserve everything, then archive

The learner writes ALL working materials to its folder as it goes (forward states, notes, every snapshot, revision log) — nothing kept only in memory. Because `/tmp` is ephemeral, at run end **archive the entire run working directory** into the project: `ingest/archive/test/<run-id>/` (drop the bulky `images/` and the copied guide/vocab — keep all agent-produced artifacts + eval). Write a `README.md` with the per-cycle CER tables (diplomatic + reading), cross-learner spread, snapshot-evolution notes, and any drops/resumes.

## Output JSON

Write `public/data/runs/<run-id>-results.json`. Beyond the `manuscript-test-run` schema, a longitudinal run records the **trajectory**, per learner:
- `run_mode`: `"single-continuous"` (completed in one context — clean) or `"relay-recovered"`, and `seams`: list of `{set, reason}` where recovery kicked in (empty for clean). Analysis should be able to filter to clean runs.
- `forward_cer_by_set` (diplomatic + reading), `postrev_cer_by_round` (diplomatic + reading), `overall` (diplomatic + reading), `modernization_cost`,
- `flag_rate_by_set` (forward-pass open-flag counts — watch for over-deferral),
- `snapshot_files` (the ordered list — the evolving theory of the hand),
- and `summary.spread` across learners (overall diplomatic + reading), computed over clean runs (note how many of N were clean).

Record everything; decide what to display later. Do not modify existing site data files or charts (same boundary as `manuscript-test-run`).

## What's different from manuscript-test-run (quick reference)

| | manuscript-test-run | this skill |
|---|---|---|
| Unit | one page | one hand, in sets |
| Agents | N parallel, independent | per learner: ONE continuous agent (single mind); learners parallel |
| State | none (fresh each) | carried in the agent's own context, mirrored to disk as snapshots |
| Drop | lose the agent | relay recovery from latest snapshot; seam logged (clean vs recovered) |
| CER | single number | per-set + per-round trajectory; diplomatic + reading |
| Output | spread across agents | trajectory + spread across (clean) learners |

Shared, unchanged: `/tmp` isolation, references out of learner folders, blind separate evaluators, integrity audit, preserve-everything, JSON-records-all.
