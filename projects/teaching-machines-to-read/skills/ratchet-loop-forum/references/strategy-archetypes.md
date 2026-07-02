# Strategy Archetypes & Allocation

The fanout's power comes from *diversity of approach*, not just count. N agents fanned from one
baseline with one prompt collapse onto the same edit. Assign each candidate a distinct **archetype**
(how it should think) plus a concrete instance (what it should try), and the round covers real ground.

## The archetypes (risk-tiered)

Risk here means variance of outcome, not danger. Low-risk arms convert reliably but cap small.
High-risk arms usually whiff but occasionally jump the metric. Because the ratchet clips losses at
zero, high-risk is cheaper than it looks.

| Archetype | Risk | What the agent does | Best when |
|---|---|---|---|
| **Refine** | low | Tighten an existing approach: a hot path, a constant, a data structure swap with the same shape. | Early, and whenever the metric is still moving. |
| **Tune** | low–med | Adjust parameters/heuristics/thresholds within the current design. | A parameterized system not yet at its setting's ceiling. |
| **Restructure** | med | Refactor a component's internals, keeping its contract. New algorithm, same interface. | Refine has plateaued but the design is sound. |
| **Subtract / ablate** | med | *Remove* something — a layer, a cache, an abstraction — and see if the metric holds. | Always keep one in rotation (see below). |
| **Generative / self-scaffold** | high | Don't apply a given rule — have the agent *build its own* intermediate representation from the paired data (an alphabet, a grammar, a guide) and optimize against that. | When hand-written rules plateau; when the problem has structure the agent can rediscover. |
| **First-principles rewrite** | high | Throw out the current approach for one component and rebuild from the problem statement. | On a plateau; when the design itself is suspect. |
| **Cross-pollinate** | high | Combine the winning changes from two prior archetypes/branches in the archive. | Mid-run, once the archive holds a few distinct winners. |
| **Wildcard** | high | An unconstrained "surprise me," seeded with a deliberately odd framing. | A long plateau where the obvious moves are spent. |

**Subtract earns its permanent slot.** It does double duty: it's a search move *and* a continuous
ablation test — does the structure recently accreted actually carry weight, or is it cruft the search
never paid to remove? It's cheap regularization against the monotonic-accretion failure mode, where a
ratcheting loop only ever adds and slowly bloats. Pair it with the rule "remove something whenever you
add something" inside other archetypes' prompts too.

The catalog is a starting point. During Phase 0, specialize instances to the domain: for a networking
protocol, Restructure might mean changing the batching/windowing; for a frontend framework, Subtract
might mean dropping a runtime abstraction; for a transcription skill, Tune might mean reweighting the
glyph-disambiguation rules. Coauthor these with the user.

## Allocation: the barbell

Spread the N candidates across archetypes as a **barbell** — cluster at the low-risk end (reliable
small wins) and the high-risk end (rare big jumps), starve the medium middle. Diversification theory
says balance to damp variance; here you *don't want* to damp variance, because the ratchet already
removed the downside variance entirely. The only thing the low-risk end insures against is a **barren
round** (every long shot whiffs and nothing promotes), so keep enough of it to make barren rounds rare,
and put the rest on lottery tickets.

A reasonable default for N=6: 2 Refine, 1 Tune, 1 Subtract, 1 First-principles, 1 Cross-pollinate/Wildcard.

## Allocation breathes with state

The mix is not fixed — it's a scheduler on the risk distribution, keyed to recent yield:

- **Improving** (recent rounds promoted): the landscape near baseline is fertile. Weight the low-risk
  end; cheap moves are converting.
- **Plateau** (K rounds without a held-out promotion): the cheap moves are exhausted. Shift weight to
  the escape archetypes (First-principles, Subtract, Cross-pollinate, Wildcard) — they're now the only
  arms with positive expected delta.
- **Endgame** (budget/iterations running low): tilt to exploit — fewer wildcards, more Refine/Tune to
  lock in the best reachable point. This mirrors an explore→exploit schedule.

## Argumentative credit (not a win counter)

The tempting primitive is a per-archetype **yield** tally — how often each archetype produced a promoted
candidate. Resist it. Counting wins is the slot-machine view, and it throws away the orchestrator's real
faculty: it reads each candidate's *justification* and *diff*, sees the gap between predicted and measured
effect, and can understand **why** something worked or failed. That understanding generalizes across the
whole universe in a way a win count never does — one richly-interpreted loss prices a whole region of
strategies you've barely sampled, which is exactly what makes a wide universe tractable.

So the credit primitive is a model of **which kinds of reasoning are tracking truth in this problem
space**, updated each round by evaluating every justification against its result:

- A candidate whose stated reason predicted its measured effect is evidence *for that line of reasoning*,
  not merely for its archetype label.
- A candidate that won for a reason other than the one it gave is a *warning* — the gain may be luck or
  an artifact, and the archetype shouldn't be credited for it.
- A candidate that lost but whose reasoning was sound (the effect was real but smaller than a rival's, or
  blocked by a fixable gate) keeps its line of reasoning alive for re-seeding.

This is the Mercier–Sperber move applied to allocation: reasoning is for *evaluating* arguments, and it
does that far better than it generates winners up front. The orchestrator is doing post-hoc argument
evaluation — its strength — rather than blindly counting outcomes. **But the same faculty is biased
toward confirming a position once it holds one**, which is why the loop pairs the orchestrator with an
independent challenger (and optionally a human) in step 4: a solitary reasoner setting its own direction
will rationalize; argument-evaluation is only reliable when proposer and evaluator are different agents.

What survives from bandit theory is the *tempo*, not the bookkeeping:

- **One-sided rewards.** The ratchet clips losses at zero, so tilt *harder* into high-variance arms than
  any portfolio rule would sanction — the drawdown they exist to avoid can't happen here.
- **Restless / non-stationary.** The landscape shifts each promotion, so reasoning that tracked truth last
  round may not now. Re-test dormant lines occasionally; don't trust a stale model.
- **Noise couples the two knobs.** The corruptible quantity is the *across-round* read of what's working —
  the multiple-comparisons demon in a new coat. The noisier the metric, the more weight the *argument*
  carries relative to the *number*, and the slower you let the allocation swing on any single result.

Keep the explore/exploit instinct from bandits; drop the regret math — the reward structure and the
credit primitive are both different animals.

## The strategy universe and the active set

The catalog above is a *starting universe*, not a fixed roster, and "go wider" is a real instinct — humans
attack a problem from far more than a half-dozen angles. Widen along two axes without starving the loop:

- **Universe vs. active set.** Let the universe of archetypes be large; keep a smaller **active set** in
  rotation each round, sized to what N candidates can actually inform. Promote and relegate between bench
  and active set on argumentative credit, and re-test a dormant archetype occasionally so its estimate
  doesn't go stale. Breadth lives in the universe; tractability lives in the active set. (This is the
  watchlist-vs-holdings distinction: you can track a thousand names and hold eight — but only because a
  research process prices the rest, which here is the orchestrator reading reasons.)
- **Generated, not enumerated.** Don't try to write the perfect taxonomy up front; most "new angles" are
  near-duplicates in *outcome* space even when distinct in prose, and the right gamut is domain-relative.
  Instead, instantiate domain-specific archetypes at setup, and let the universe **grow at runtime**: when
  a winning candidate uses a move that fits no existing archetype, name it and add it with its observed
  risk profile. The catalog accretes from evidence, not a priori — the generative-beats-accumulation
  principle applied to the strategy vocabulary itself.

Two guardrails so a large universe stays useful rather than just large:

- **Orthogonality screen.** Measure pairwise diff-distance between candidates of different archetypes;
  merge archetypes that keep collapsing onto the same changes. You want the universe *distinct*, not big.
- **Risk-axis placement.** Every archetype, new or old, must slot somewhere on the low-to-high variance
  axis the barbell needs — or it fattens the medium middle the allocation is trying to starve.

## Search topology: single-lineage vs population

**Single-lineage (default).** One baseline, one ratchet. Every round's fanout branches from the single
current baseline; the best confirmed candidate becomes the new baseline. Simple, cheap, and correct for
smooth-ish landscapes. Its weakness is greed: it hill-climbs and can wedge into a local optimum that no
single cheap move escapes.

**Population / island model (toggle on for rugged landscapes).** Maintain `m` distinct lineages
(islands), each with its own baseline. Each round, allocate the fanout across islands, ratchet each
island independently, and add two cross-island moves:

- **Cross-pollinate.** Breed a candidate from the winning changes of two different islands — this is the
  archetype that needs a population to feed it. It's how genuinely different basins combine.
- **Migration / extinction.** Periodically, a strong island can seed a copy into a weak island's slot
  (the weak lineage goes extinct). This keeps compute on live basins without fully collapsing diversity.

Keep islands **diverse on purpose** — seed them from different first-principles rewrites, or pin each to
a different region of the space — or they converge and you've paid m× for one lineage. The cost is real:
m baselines means roughly m× the validation. Turn it on when the user expects several viable approaches
(a protocol with competing architectures, a framework with rival rendering strategies), not for a
problem with one obvious design to refine.

The archive in the single-lineage case is the lightweight shadow of this: keeping top-m losers around
gives you cross-pollination material and escape routes without paying to run m full lineages. Reach for
the full island model only when single-lineage demonstrably plateaus below the target.
