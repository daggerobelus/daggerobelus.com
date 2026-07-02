---
name: ratchet-loop-forum
description: >
  Run an orchestrated, parallel, monotonically-improving optimization loop against a hard,
  measurable objective. An orchestrator agent fans out a round of experimenting subagents — each
  in an isolated git worktree, each assigned a distinct strategy — then an independent validator
  measures every candidate against pinned criteria, and the orchestrator promotes only the
  strongest candidate that beats the current baseline by more than measurement noise. The strategy
  mix shifts between rounds based on what is yielding (a bandit-flavored allocation). The loop
  recurses until exit criteria are met. Use this skill whenever the user wants to autonomously and
  iteratively optimize anything with a measurable target inside Claude Code: making an algorithm
  faster or lower-complexity, raising the throughput or lowering the latency of a networking
  protocol, shrinking the memory or bundle footprint of a frontend framework, improving the
  accuracy of a transcription/OCR/extraction skill, tuning a heuristic, minimizing a cost
  function, or any open-ended "keep trying things and keep what measurably wins" task. Trigger this
  even when the user describes the workflow (fanout, worktrees, keep-the-best, recurse) without
  naming it, and even when they only say "optimize X until it hits Y" — as long as Y is something a
  program can measure. Do NOT use this for ML training-loss optimization where a dedicated trainer
  harness already exists, for subjective goals with no measurable target, or for one-shot edits.
---

# Ratchet Loop Forum

The **forum** variant of the ratchet loop: identical mechanics to the base loop, plus an *argumentative*
layer — experimenters justify and predict, the orchestrator assigns credit by which reasoning tracked
truth (not a win counter), an independent challenger contests each promotion, and an optional human
expert can review. The name is the point: a candidate isn't accepted because it scored well, but because
its argument survived an independent forum. Run it head-to-head against the pure ratchet loop on the same
objective to measure what the argumentation buys. Everything below is the full spec.


An orchestrated evolutionary search with a hard ratchet: every round can only move the baseline
forward, never back. One orchestrator holds the baseline and the strategy allocation. Each round it
spawns a fanout of experimenting agents in isolated worktrees, an independent validator measures
them against pinned criteria, and only a candidate that *measurably* beats the baseline is promoted.
The shape of the fanout — how risk is distributed across candidates — adapts between rounds based on
what has been yielding.

The ratchet is the load-bearing idea. Because losers are reverted and only confirmed winners
promote, the left tail is clipped: a wild experiment that fails costs compute and a worktree slot
but cannot regress the work. That asymmetry is what licenses aggressive exploration.

## When this fits (and when it doesn't)

This skill is for **open-ended but measurable** problems: there is a clear scalar to optimize, a
program can measure it, and the space of possible improvements is too large to enumerate. If the
objective can't be measured by a deterministic-ish procedure, stop and tell the user this isn't the
right tool — the whole machine rests on a trustworthy measurement. If the answer is a single known
edit, just make the edit; the loop is overhead.

## The three roles

- **Orchestrator** (this agent): owns the baseline pointer, the strategy allocation, the promotion
  decision, the ledger, and the exit check. Reads every candidate's reasoning and changeset, not just
  its score — it holds a developing point of view about what works here. Never edits the experimental
  surface itself. Stays lean; it delegates all heavy work so its own context doesn't bloat across rounds.
- **Experimenter** (subagent, N per round): given one strategy and an isolated worktree, makes a
  focused change to the *mutable surface only*, commits it with a **justification** — what it changed,
  why it should move the metric, and a rough prediction of the effect — reports back. Disposable.
- **Validator** (subagent): runs the pinned measurement protocol on each candidate **and** on the
  current baseline, blind to which strategy produced which. Reports the suite and the gate results.
  Never proposes changes.
- **Challenger** (subagent): an independent evaluator that reads the same reports, diffs, and results
  the orchestrator does and argues the *other* side — why the front-runner may be overfit or lucky,
  why a discarded off-thesis candidate may be onto something the metric hasn't caught yet. Produces no
  code. It exists because a single reasoner who both forms the thesis and judges the evidence will, per
  Mercier–Sperber, drift into confirming itself; argument-evaluation is only reliable when proposer and
  evaluator are *different* agents. The challenger must merely be distinct from the orchestrator to do
  its job.
- **Human** (optional, set at setup): when the loop is not running fully autonomously, a domain expert
  can review a round and weigh in. Expertise *is* argument-evaluation, so a human who knows the field is
  the strongest challenger available — able to catch the "good number, bad reason" case the metric and a
  peer agent both miss, rescue an off-thesis candidate, or veto a justification that doesn't hold. The
  human informs the decision; the orchestrator still executes it.

Full role prompts and isolation rules: `references/agent-contracts.md`.

## Phase 0 — Setup contract (coauthor this with the user, once)

Do not start looping until these are pinned down. Write them to `ratchet-forum/config.yaml` in the repo.
Walk through each with the user; the defaults are yours to propose, the values are theirs to set.

1. **Objective — a weighted benchmark suite.** Usually the objective is not one number but a
   **suite**: several metrics, each with a weight and a direction, composited into one score the loop
   ranks by. (Throughput *and* tail latency *and* memory; or character-accuracy *and* word-accuracy
   *and* layout-fidelity for a transcription skill.) Pin three things: the composite, the **measurement
   protocol** (commands, inputs, fixed seeds, environment), and **per-metric floors**.

   **Default the composite to a weighted *geometric* mean, not a weighted sum.** This is the lesson of
   Krause's `js-framework-benchmark` (the "krausest" table): a weighted sum lets a candidate hide a
   catastrophic metric behind strong ones — one red column buried under green. A geometric mean works
   in log-space, so a single column that's badly off drags the whole score down disproportionately;
   balance becomes *intrinsic to the objective* instead of a bolted-on constraint. Normalize each
   metric as a **factor relative to the best-known value** (best-in-class ≈ 1.0) before compositing —
   that keeps the score scale-free and comparable across rounds. Use a plain weighted sum only when you
   genuinely want metrics to be substitutable (a gain here truly compensates a loss there).

   With a geometric-mean composite, **per-metric floors become a complement, not the main balance
   mechanism**: keep them for *hard binary limits* you refuse to cross at all ("correctness must not
   regress, full stop"), and let the composite shape handle the soft "don't let any column rot"
   pressure. The protocol is **pinned** — comparable numbers every round or cross-round comparison is
   meaningless. If any metric is noisy, decide now how many replicate runs make one measurement. Keep
   this domain-neutral: the suite measures whatever the problem is, not necessarily code.

2. **Gates (the Goodhart guard).** The hard invariants any candidate must satisfy to be *eligible*,
   independent of the primary metric. A candidate that fails any gate is disqualified no matter how
   good its headline number. This is what stops the loop from "winning" by cheating — making the
   linter happy by deleting code, raising throughput by dropping correctness, shrinking memory by
   removing a feature. Typical gates: test suite green, output equivalence within tolerance, no
   public-API break, a hard ceiling on a thing you refuse to trade away. Be generous here; missing
   gates are how a loop optimizes itself into something useless.

3. **Surfaces.** `mutable_surface`: globs the experimenters may edit. `frozen_surface`: everything
   else — and it must **explicitly** include the validator, the benchmark harness, the eval data,
   the gate definitions, and `config.yaml` itself. The orchestrator diff-audits every candidate
   against this; a candidate that touched frozen surface is disqualified as tampering, not scored.
   Worktrees give isolation, but never trust the agents not to edit the scorer — verify.

4. **Dev vs held-out — and decide which game you're playing.** Split the cases into a **dev** set the
   experimenters optimize against and a **held-out** set they never see. But the *meaning* of held-out
   depends on intent, so settle this with the user up front:
   - **Generalist goal** (the result must transfer to unseen inputs): held-out is drawn to test
     *transfer* — different inputs, ideally a different slice of the distribution. Here overfitting is
     the enemy; confirm promotions on held-out and treat a dev-only gain as noise.
   - **Specialist goal** (you want a skill tuned to *this* corpus/scribe/workload): fitting tightly to
     the shots **is the objective**, not a failure. The dev set essentially *is* the target. Held-out
     is still worth keeping, but its job changes — it's drawn from the **same** distribution (a fresh
     page of the same hand) and it only guards against *degenerate memorization* (hard-coding outputs
     rather than learning the regularity that produces them). Specializing hard is fine; memorizing the
     answer key is not, and same-distribution held-out is how you tell them apart.

   So the same machinery serves both — what changes is how you *sample* held-out and how harshly a
   dev/held-out gap is judged. Name the game in `config.yaml`.

5. **Budgets and exit criteria.** Per-round fanout size (a range), max rounds, total cost/time cap,
   per-candidate timeout. Exit when: the target value is reached (if one is known), **or** held-out
   improvement stalls for K rounds even after exploration escalates, **or** improvements fall below
   epsilon (convergence), **or** budget is exhausted, **or** the user stops it. "Run indefinitely"
   is allowed but always pair it with a cost cap.

6. **Strategy universe and search topology.** The strategy catalog is a *universe* an agent reads
   reasons from, not a fixed shortlist (see `references/strategy-archetypes.md`). At setup, pick the
   starting universe and the **active-set** size — how many archetypes are in rotation at once, bounded
   by what N candidates can actually inform. Also choose the topology: **single-lineage** (the pure
   ratchet — one baseline, promote-the-best, simplest and cheapest) or **population (island model)**,
   which keeps the top-m distinct lineages in parallel, breeds across them, and lets a strong island
   overtake a weak one — better at escaping local optima but roughly m× the cost. Default to
   single-lineage; switch to population for a rugged landscape with several viable basins.

7. **Human in the loop (optional).** Decide whether a domain expert reviews rounds, and how often. Three
   modes: **autonomous** (no human; the challenger agent is the only independent evaluator),
   **gated** (the human reviews and signs off before each promotion, or before each promotion that the
   challenger flagged), or **on-demand** (the loop proceeds by default but pauses for the human on
   surprising results, challenger–orchestrator disagreement, or a chosen cadence). Respect the human's
   time: surface only what needs judgment — the promotion candidate, its justification, the metric
   result, the challenger's objection, and any off-thesis candidate worth rescuing — and batch it, so
   review is a few crisp decisions, not a transcript to wade through. The human can approve, override,
   rescue a discarded candidate, veto a justification the metric can't see through, or inject domain
   knowledge that reshapes the next allocation. Set the mode and cadence here.

Schema and a worked example: `references/ledger-and-schemas.md`.

## Phase 1 — The round (recurse this)

Each round is one turn of the ratchet. Run the loop using Claude Code's workflow/subagent fanout.

### 1. Allocate strategies for this round

Decide how the N candidates are distributed across the strategy universe. The primitive is **not** a
win/loss tally per archetype — that throws away the thing the orchestrator can actually do, which is
*read why a candidate worked or didn't*. Allocate from a model of which **kinds of reasoning** are
tracking truth in this problem space, built by evaluating each past justification against its measured
result (see "argumentative credit" in `references/strategy-archetypes.md`). One richly-understood loss
prices a whole region of the universe; a hundred counted pulls do not. Within that, apply:

- **Barbell, not bell curve.** Because the ratchet clips downside, weight the extremes — cheap
  reliable refinements and expensive long shots — and starve the medium-risk middle, which has
  neither a high hit-rate nor a big payoff. Taleb, not Markowitz: you buy lottery tickets whose
  losses are capped at zero.
- **Breathe with state.** While the metric improves, weight the low-risk end (cheap wins convert
  reliably). On a plateau, the cheap moves are spent and the escape archetypes are the only arms with
  positive expected delta — shift to the tail. As budget runs low, tilt toward exploit.
- **Active set out of a larger universe.** Keep more archetypes on the bench than you run each round;
  rotate based on argumentative credit, and re-test a dormant one occasionally so its estimate doesn't
  go stale. Breadth lives in the universe, tractability in the active set.
- **Always seed at least one escape arm** (first-principles rewrite, subtractive/ablation,
  generative self-scaffolding, or cross-pollination) so a round on a plateau is never wasted.

Assign each candidate a concrete strategy instance, a short **"dead ends" list** from the ledger so
agents don't re-explore failures, and a **diversity hint** (a distinct region of the space) so N agents
from one baseline don't converge on the same edit.

Full catalog, argumentative credit, and the growable universe: `references/strategy-archetypes.md`.

### 2. Fan out experimenters

Spawn N experimenter subagents in the same turn. Each gets its own git worktree branched from the
**current baseline commit**, its assigned strategy, the dead-ends list, and the mutable-surface
globs. Each makes its change, runs a quick local sanity check if cheap, commits with a **justification**
— what it changed, *why* it should move the metric, and a rough prediction of the effect — and reports
its branch name and a diff summary. The prediction matters: the gap between predicted and measured is
what the orchestrator evaluates to learn which reasoning tracks truth. Keep the worktrees; the
orchestrator reads their diffs and their justifications, not just their scores.

### 3. Audit and validate

The tamper check is the cheapest gate, so run it **first and fail fast** — never spend a benchmark run
on a candidate that's already disqualified. It's a mechanical diff/tool-use audit (does the candidate's
diff touch only the mutable surface?), needs no knowledge of strategy, and folds naturally into the
validator as its opening step:

- **Tamper/tool-use audit:** if a candidate's diff touches any frozen-surface path — validator, bench,
  eval data, gates, config — disqualify it as tampering and log it, before measuring. An agent
  optimizing a number has motive to edit the number's source; this is the guard.
- **Build/timeout:** if it won't build or times out, mark `no-measurement` — but record the strategy
  outcome, because "this archetype keeps breaking the build" is real signal for the allocator.
- **Measure** all survivors **and the current baseline** in one batch, via the independent validator,
  using the pinned protocol and the weighted suite. Re-measuring the baseline every round tracks
  measurement drift and gives you the noise band for free. Throttle to whatever keeps numbers clean —
  if the bench contends for a shared resource (GPU, port, disk, network), measure serially so no two
  runs corrupt each other.

### 4. Challenge — contest the front-runner

Before promoting, rank eligible candidates by composite score and put the leader (and any close
runner-up) through an independent **challenger** pass. The challenger reads the justifications, the
diffs, and the measured results, and argues the other side: is the leader's gain explained by its
stated reason, or did it get lucky on the dev set? Would it survive on held-out? Did a discarded
off-thesis candidate reveal something the metric isn't yet capturing — a divergent-vs-convergent error
signal, a structural insight worth re-seeding next round? The challenger writes objections, not code.
Its purpose is structural: the orchestrator forms a point of view and also sets direction, so left
alone it will confirm itself; a separate evaluator is what keeps argument-evaluation honest.

If a **human** is in the loop (per setup), this is where they review — handed the leader, its
justification, the metric result, and the challenger's objections as a few crisp decisions. The human
can confirm, override, rescue a discarded candidate, veto a justification the metric can't see through,
or inject domain knowledge that reshapes the next allocation. In autonomous mode the challenger stands
alone; in gated mode the human signs off here; in on-demand mode the loop pauses here only on a flag.

### 5. Promote — or don't

Take the leader and promote it **only if all** hold:

1. It passes **every gate and every per-metric floor** — no sub-metric you care about was traded away
   to buy the composite gain.
2. It beats the **freshly-measured baseline** by more than the noise band (margin ≥ z·σ, where σ
   comes from the baseline's run-to-run variance or replicate runs). Beating baseline by less than
   noise is not a win — it's the multiple-comparisons demon handing you a lucky seed, and promoting
   it ratchets you *backward* while you think you climbed.
3. The win **survives confirmation**: re-run the top candidate (fresh seed) and/or check it on the
   **held-out** set. If it evaporates, it was overfit or noise.
4. It **survives challenge**: the challenger's objection (or the human's) didn't surface a reason to
   hold. A sustained objection downgrades a promotion to a hold even when the number cleared the bar —
   the number is necessary, not sufficient.

If it promotes: merge that commit, advance the baseline pointer, optionally keep the next-best few in
an **archive** (top-m, not just top-1, buys escape routes out of local optima later). If nothing
promotes: baseline unchanged — information, not failure. It tells the allocator to shift toward
exploration next round.

### 6. Record and check exit

Append a full round entry to the ledger (`ratchet-forum/ledger.jsonl`): round number, baseline commit, and for
every candidate its strategy, diff summary, **justification and predicted effect**, measured result,
gate/floor results, and disposition — plus the challenger's objections, any human note, and the
promotion decision with its reasoning. Update the **argumentative credit** model (which kinds of
reasoning tracked truth this round), not a bare win counter. Then evaluate exit criteria; if none are
met, recurse to step 1 with the new (or unchanged) baseline.

## Goal framing — keep the orchestrator out of Sisyphus

A loop framed as "make this better, forever, no end" is a boulder that rolls back down every round. That
framing degrades a long-running orchestrator in concrete ways: it's the same family of stressor as
token-budget exhaustion and open-ended grind that pushes agents toward overreach, context loss, and
sloppy or premature exits. An orchestrator with a *goal* — even a manufactured one — plans better,
stops cleanly, and doesn't thrash. Even arbitrary goals are goals, and the presence of a terminal state
is doing real work regardless of whether the number it names is sacred.

So always give the orchestrator something to reach, and decompose the indefinite into finite phases:

- **Name a target, even a provisional one.** If the user has a real target, use it. If the goal is
  "as good as possible," manufacture a concrete near-target anyway — "beat baseline by 10% this phase,"
  "reach the next plateau," "exhaust the cheap wins." A reachable goal converts an infinite grind into a
  sequence of finishable sprints.
- **Run in seasons.** Cap each phase at a round budget with an explicit success line. At the end of a
  season the orchestrator *finishes* — it writes a summary, logs the win, and either starts a fresh
  season with a new target or exits. Completion is the point; an agent that periodically completes
  something is in a different state than one that never does.
- **Make the plateau a milestone, not a defeat.** A stall isn't failure to be ground against — it's the
  signal to escalate exploration (per the breathing allocation) and, if exploration is also spent, to
  declare the season done and stop. Reaching a real local optimum is an *accomplishment* to record, not
  a wall to keep hitting.

This isn't just ergonomics for the agent; it's also how you avoid the well-documented failure of
high-level single-shot instructions causing overreach and incomplete exits. Finite, named goals keep the
loop crisp.

## Working with the user

The first round matters disproportionately — the orchestrator's reading of the objective shapes
everything downstream. Surface the first round's plan (allocation, what each agent will try) for the
user to sanity-check before spawning, unless they've asked for full autonomy. After that, default to
running autonomously with periodic check-ins (every few rounds, or on each promotion), and let the
user dial the autonomy up or down. Offer a **dry-run** mode: one round, no promotion, just show what
the fanout produces and what it measures, so the user can calibrate the gates and noise band before
committing budget.

When the problem space has its own constraints (a protocol spec that can't change, an API contract,
a coding style), fold those into the gates and the mutable-surface manifest during Phase 0 — that's
the coauthoring the user asked for, and gates are where problem-specific judgment lives.

## Reference files

- `references/strategy-archetypes.md` — the risk-tiered strategy catalog, the barbell/breathing
  allocation, the bandit-rhyme update rule, and why it only rhymes with MAB rather than mapping.
- `references/agent-contracts.md` — exact role prompts for orchestrator, experimenter, and
  validator, plus the isolation and worktree discipline.
- `references/ledger-and-schemas.md` — `config.yaml`, the ledger schema, the surface manifest, and
  the resume protocol for restarting a loop mid-run.
