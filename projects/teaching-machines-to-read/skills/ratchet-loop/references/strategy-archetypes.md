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

## The bandit rhyme (and where it breaks)

Track per-archetype **yield**: how often each archetype produced a promoted candidate, and the average
margin when it did. Each round, reallocate toward high-yield archetypes — *but damp the reallocation
rate by measurement noise*. The noisier the metric, the slower you're allowed to shift, because a noisy
metric makes two lucky rounds look like a hot archetype, you over-allocate, the landscape moves under
you, and your estimate is already stale.

This is why it only **rhymes** with a multi-armed bandit rather than mapping cleanly:

- **One-sided rewards.** The ratchet clips losses at zero. A bad pull costs compute, not metric. So
  tilt *harder* into high-variance arms than any standard bandit/portfolio rule would sanction — the
  thing they exist to avoid (drawdown) is structurally impossible here.
- **Strategy classes, not actions.** The specific candidate is regenerated and discarded each round.
  What persists and accrues evidence is the *archetype*, not any concrete edit — so credit assignment
  lives one level up.
- **Restless / non-stationary.** The landscape changes every time you promote a new baseline, so
  arm values genuinely drift. This is why estimates go stale and why the noise-damped reallocation
  rate matters.
- **Batched, with free within-round credit.** The fanout gives clean independent per-candidate
  measurement *within* a round — that credit is free and exact. The corruptible quantity is the
  *across-round* archetype value. That's the multiple-comparisons demon from promotion, wearing a
  portfolio costume: more candidates and more rounds mean more chances for noise to crown a false
  favorite. Couple the promotion margin and the reallocation rate to the same σ.

Steal the explore/exploit intuitions and the "shift faster when estimates are confident" instinct from
bandit theory. Don't import its regret math literally — the reward structure isn't the same animal.

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
