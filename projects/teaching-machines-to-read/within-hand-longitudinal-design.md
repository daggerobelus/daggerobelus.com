# Within-Hand Longitudinal Transcription — Design Spec

**Date:** 2026-06-16
**Project:** Teaching Machines to Read (`projects/teaching-machines-to-read/`)
**Status:** Design draft for review.

---

## 1. Research question

As an agent works through a *single scribal hand* page by page — refining its *own* accumulating alphabet/notes as it goes — does it **read that hand better over time**?

**CER remains the primary metric.** Alongside it, we track how the agent's reading of the hand develops: what it learns about how this scribe forms letters, visible in the growing alphabet/notes and the record of revisions.

This extends the project's central finding (agents learn like students, Chapter 2) onto a new axis: not learning across *interventions*, but learning through *sustained exposure to one hand*.

## 2. Relationship to prior findings

- **Generation effect** (Ch. 2): the agent grows and reuses *its own* alphabet — it generates the notes it relies on rather than receiving them. This keeps the method on the "generation" side of the established result.
- **Gap honesty** (current skill): the `[word?]` / `[...]` markers the forward pass produces are exactly the targets the revision pass returns to. Honest gaps are the *mechanism* that makes revision possible, not a separate feature.
- **Post-hoc revision "doesn't work"** (Runs 5, 9): that failure was *whole-work re-review with no new information* → rubber-stamping. This revision is different: **targeted** (only flagged spans) and **driven by new knowledge** (the agent's maturer reading of the hand). The design must *instrument* this distinction (see §4), not assume it.
- **Run 13 over-gapping** (cautionary): heavy "mark gaps, don't guess" emphasis caused agents to transcribe only ~half of a hard page (64–74% CER). The "you'll get to revise later" framing risks amplifying over-deferral. **Forward-pass flag rate is a monitored quantity.**

## 3. Protocol

One generative process per hand, built on the proven core — alphabet-first + vocabulary verification + gap-honesty — applied uniformly to every page.

**Set size: 5 pages**, anchored to the project's "sweet spot" finding.

**Per-hand cycle:**

```
for each set of ~5 pages (in manuscript order):
    1. FORWARD PASS — transcribe the set using the current alphabet/notes.
       Flag uncertainties honestly ([word?], [...]). Instructions state
       explicitly that flagged spans get a dedicated revision pass later —
       deferring is the correct move, not a failure.
    2. CONSOLIDATE — update the alphabet/notes with new knowledge of the
       hand learned from this set. Write a NEW numbered snapshot
       (alphabet-after-set-NN.txt) — never overwrite the prior one, so the
       full evolution is preserved as a sequence of files.
    3. ROLLING REVISION — revisit still-open flagged spans from ALL prior
       sets using the updated notes. For each revisit, log before → after
       and what changed in the reading of the hand.
(after the final set) optional FINAL REVISION pass with the fully matured notes.
```

**Generation guardrail:** the alphabet/notes the agent carries forward are always *its own*. Nothing externally authored is fed in.

## 4. Measurement

**Primary (CER):**
- **Per-set forward CER** (before revision) across the set sequence → does the agent read *new* pages better as its notes mature? (The within-hand learning signal.)
- **Post-revision CER per rolling round** → does returning to old flagged spans with maturer notes improve them?
- **Whole-hand final CER** vs. the project's existing single-page-independent results → does cumulative-with-revision beat independent-page transcription?

**Revision integrity (guards against rubber-stamping):**
- For each revised span, does the edit move it *toward* or *away from* the reference? Systematic toward = learning; churn = the old rubber-stamp failure reproduced.

**Behavioral / artifact:**
- **Forward-pass flag rate** per set (watch for over-deferral).
- **Alphabet/notes snapshots**, one retained file per set (how the agent's reading of the hand develops — the sequence is meant to be read directly, e.g. diffed set-to-set), and the **revision log** (where/why a reading changed). These are first-class research outputs, not scratch files — see §7 for preservation.

CER computed with the existing `compute_cer.py` (jiwer); stats with `compute_stats.py` (scipy). **Blind protocol preserved, with one cumulative-specific safeguard:** the transcribing agent and the evaluating agent are separate — the transcriber sees the page image + its own notes (never the reference); the evaluator sees the transcription + reference (never the image). Critically, because this run is *sequential*, evaluation runs **out-of-band** and per-set/per-round CER is **never surfaced back to the transcribing agent between sets**. Otherwise the agent would learn the hand from the *reference* rather than from its own reading — contaminating the entire learning signal (cf. the project's "agents cheat when they can / shared folders contaminate" lesson). The carried alphabet/notes grow from page images + the agent's own prior work only.

## 5. The skill

A **new cumulative-generative transcription protocol** (a SKILL.md variant), distinct from `manuscript-transcription`:
- Inherits: alphabet-first, vocabulary verification (confirm-don't-generate), gap-honesty conventions, Folger semi-diplomatic output.
- Applies the method uniformly to every page (no Standard/Scaffolded triage branch).
- Adds: the set-based forward pass, per-set consolidation with snapshotting, and the rolling-revision pass with before→after logging.
- Writes **all** its working materials (every transcription state, notes, snapshot, log) to the run folder as it goes — nothing kept only in working memory — so the archival step (§7) captures the complete record.

This is the "use the skills function more" piece: the experiment runs *through* a versioned skill, orchestrated by `manuscript-test-run` extended for sequential set-based execution (vs. its current parallel-independent agents).

## 6. Corpus

**v1 subject: Lady Sedley MS534** (1686), FromThePage work `55048`.
- Downloaded to `ingest/archive/sedley-ms534-full/` — **40 content pages** (pages 2–42, skipping blank/near-blank 40; 1 and 43–45 are front/back matter). Each page has a paired reference transcription.
- **40 content pages = 8 sets of 5.**
- Single, legible hand → low-headroom, so a conservative first test (the learning curve has less room to bend than on a hard hand, but it's the clean, known starting point).

**Future corpus expansion** (note only — *not* in v1; chosen for gynecological-content value so transcription output also serves the recipe-books / dissertation research):

| ms_id | Attribution | FromThePage work | Pages (all referenced) | Note |
|---|---|---|---|---|
| saint-ms4338 | Johanna Saint John ("I S"), 1680 | `25010759` | 207 | Highest gyn density; richest target — **confirm single hand across 207pp** |
| brumwich-ms160 | Anne Brumwich & others, 1663 | `25002909` | 139 | Multi-hand → hand-boundary natural experiment, not a clean single-hand run |
| jane-jackson-373 | Jane Jackson, 1642 | `32142178` | 143 | Content-rich but water-damaged → sterner test than fair test |
| regiment-ms674 | 1625, institutional | *(work id TBD)* | TBD | Virginity outlier (16 hits) |
| catchmay-ms184a | undated | *(work id TBD)* | TBD | Broad sampler |
| surgerie-ms688 | Henslow, 1601 (scribe Plowden) | `32175110` | TBD | Known from TMTR; easy hand |

The harder gyn-dense manuscripts (Saint, Brumwich, Jane Jackson) are where within-hand accumulation has the **most room to show an effect** — so content priority and experimental payoff align for the expansion phase.

## 7. Autonomy (unattended runs)

Hard requirement: once a hand is launched, the full cycle runs to completion with **no permission prompts**.
- Runs execute in `/tmp/manuscript-runs/<run-id>/` — outside the project (preserves blind isolation: agents can't reach references or other agents' work) **and** inside the pre-approved permission sandbox.
- Project `.claude/settings.json` allowlist updated (2026-06-16) to add `Task`, `Agent`, `Bash(mv:*)`, `Bash(seq:*)`; the rest (`python3`, `mkdir`, `cp`, bare `Read`/`Write`/`Edit`, `/tmp/manuscript-runs/**`) was already permitted.

**Artifact preservation (required).** *Everything the agent produces is research data and is preserved by default* — not just the final transcription, but every intermediate the agent makes: per-set forward transcriptions (pre- and post-revision), the numbered alphabet/notes snapshots, flagged-uncertainty notes, the revision log, and the per-set/per-round CER results. Because `/tmp/` run dirs are ephemeral and get cleaned, the orchestration archives the **entire run working directory** out of `/tmp/` into a durable project location (e.g. `ingest/archive/test/<run-id>/`) at run end. **Default to keeping everything; prune nothing silently.** The point is that the full record of how the agent worked — not only its output — is reviewable after the run.

## 8. Open items / step zero for implementation

1. **Author the cumulative-generative SKILL.md** (forward pass + consolidation + rolling revision + logging).
2. **Extend `manuscript-test-run`** for sequential set-based execution with carried state (vs. parallel-independent), including the end-of-run archival of the **entire run working directory** out of `/tmp` into the durable run folder (§7).
3. **Confirm reference quality/format** of the 40 Sedley pages (FromThePage text vs. the agent's semi-diplomatic conventions — alignment for CER).
4. **Define the run artifacts/JSON schema**: per-set forward CER, per-round post-revision CER, flag rate, span-level before→after, alphabet/notes snapshots.
5. (Optional) decide whether to re-fetch page 40.

## 9. Out of scope for v1

Corpus beyond Sedley; "evaluation of learning outside CER" (Chapter 2's closing horizon — noted, but CER stays primary here).
