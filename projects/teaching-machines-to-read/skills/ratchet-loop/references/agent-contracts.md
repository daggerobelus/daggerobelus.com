# Agent Contracts

Three roles, strictly separated. The separation is a safety property, not just tidiness: the agent
that *measures* must never be the agent that *changes*, or the loop can optimize by editing its own
scorer.

## Orchestrator (the agent running this skill)

Owns: the baseline commit pointer, the strategy allocation, the ledger, the archive, the promotion
decision, the exit check. Spawns experimenters and the validator; never edits the mutable surface
itself. Stays lean — it reads diff *summaries* and metric *numbers*, not full candidate diffs or full
benchmark logs, so its context doesn't accumulate across rounds. Offload anything heavy to a subagent.

Each round, the orchestrator: (1) computes the allocation; (2) spawns the fanout; (3) dispatches the
validator, which audits-then-measures; (4) applies the promotion rule; (5) writes the ledger and checks
exit. It is the only role that merges commits or moves the baseline.

## Experimenter (spawn N per round, in one turn)

Prompt template:

```
You are an experimenter in a ratchet-loop optimization.

Baseline commit: <SHA>
Your worktree: <path>            # already created, branched from baseline
Your strategy: <archetype> — <concrete instance>
Mutable surface (edit ONLY these): <globs>
Do NOT touch (instant disqualification): the validator, benchmark harness, eval data,
  gate definitions, ratchet/config.yaml — anything outside the mutable surface.
Dead ends already tried (do not repeat): <list from ledger>
Diversity hint: <the region of the space this candidate owns>

Objective: <minimize|maximize> <metric>, measured by <one-line protocol summary>.
Gates your change must not break: <gate list>.

Make ONE focused change in the spirit of your strategy. If you add something, consider removing
something. Run the cheap local sanity check if one exists. Commit to your branch with a one-paragraph
rationale: what you changed, why you expect it to move the metric, and what it might cost.
Report: your branch name, a short diff summary, and any gate you're unsure about. Do not run the
official benchmark — that's the validator's job, and self-measurement biases the loop.
```

Experimenters are disposable. They do not see other candidates and do not negotiate — diversity comes
from their assigned archetype and region, not from coordination.

## Validator (spawn once per round; measures all candidates + baseline)

Independent and blind: it receives a set of branches/worktrees to measure, *without* being told which
strategy produced which, so it can't flatter a favored approach. It runs the **pinned protocol**
identically on every input including the current baseline, and reports raw numbers only. Its first step
is the cheapest gate — the tamper/tool-use audit — so disqualified candidates never cost a benchmark run.

```
You are the validator. You measure; you never change code.

Step 0 — tamper/tool-use audit (fail fast, before measuring):
  For each candidate, diff it against the baseline. If it touched ANY frozen-surface path
  (validator, bench harness, eval data, gate definitions, ratchet/config.yaml), mark it
  `disqualified:tamper` with the offending path and skip it. Do not measure tampering candidates.

For each surviving worktree AND for the baseline worktree:
  1. Run exactly: <pinned measurement command(s)> with seeds <fixed seeds>.
  2. Record every sub-metric in the suite (run <R> replicates if noisy; report mean and spread),
     then the weighted composite.
  3. Run each gate AND each per-metric floor; record pass/fail and evidence for any failure.
Report a table: worktree id -> {sub-metrics, composite, replicate spread, gate+floor results}.
Nothing else. If a worktree fails to build or times out, report `no-measurement` with the error —
do not guess a number. Run measurements serially if they contend for shared resources (ports, GPU,
disk, network), so no two runs corrupt each other's numbers.
```

## Worktree discipline

- One worktree per candidate, branched from the current baseline commit, created by the orchestrator
  before the experimenter is spawned. Parallel worktrees are the isolation primitive — candidates
  never see each other's edits.
- After the round, tear down losing worktrees but **keep their commits referenced in the ledger** (and
  in the archive if top-m). The code is discarded; the *information* — what was tried, what it scored —
  is retained, so future rounds don't re-explore dead ends. Discarding the information is the single
  biggest waste mode in a loop like this.
- The orchestrator's diff-audit is the real isolation guarantee. Worktrees prevent accidental
  cross-contamination; the audit catches a candidate that edited the scorer, whether by accident or
  because editing the thing that computes the metric is an easy way to "improve" it. Audit every
  candidate, every round, before it's eligible to promote.

## Resourcing reality

Propose is cheap and parallel; measure is often expensive and serial. The effective fanout width is
bounded by validation throughput, not by how many experimenters you can spawn. Fan out wide on
proposals, throttle the validator to keep numbers clean, and let the validator be the pacing bottleneck.
