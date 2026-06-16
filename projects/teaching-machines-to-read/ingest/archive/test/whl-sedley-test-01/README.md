# Run: whl-sedley-test-01 (Within-Hand Longitudinal — first test)

**Date:** 2026-06-16
**Skill:** `manuscript-transcription` (unified cumulative-generative version)
**Spec:** `projects/teaching-machines-to-read/within-hand-longitudinal-design.md`
**Purpose:** First end-to-end validation of the within-hand longitudinal protocol (sets → forward → consolidate/snapshot → rolling revision), with per-cycle blind CER.

## Setup
- **Manuscript:** Lady Sedley MS534 (1686), FromThePage work 55048. First 15 image pages (002–016).
- **Page 002 excluded from CER** — flyleaf/ownership matter in later hands, not the recipe hand. Recipe hand runs 003–016 (recipes I–XLI).
- **Sets:** set 1 = 003–006, set 2 = 007–011, set 3 = 012–016.
- **Learners:** 3 launched (single continuous agent each); **learner 3 lost** (socket drop mid-set-1, partial work later deleted — counted as lost). Learners 1 & 2 completed (learner 1 stalled at final-assembly but all substantive artifacts intact).
- **Evaluation:** separate blind eval agent per learner (`compute_cer.py`), never saw images.

## Results (raw CER — see caveat)

| | Set 1 fwd | Set 2 fwd | Set 3 fwd | Round 1 | Round 2 | Round 3 | **Overall** |
|---|---|---|---|---|---|---|---|
| Learner 1 | 9.03% | 10.81% | 8.37% | 9.07% | 10.04% | 9.44% | **9.44%** |
| Learner 2 | 9.53% | 10.50% | 8.63% | 9.56% | 10.09% | 9.58% | **9.58%** |

**Cross-learner spread (overall): 0.14 pp** — very tight consistency. Identical set-by-set shape (set 2 worst, dragged by hard page 007; set 3 best).

## Findings
1. **Pipeline works end-to-end** — the cumulative protocol ran correctly (forward → numbered snapshot → rolling revision), artifacts preserved, per-cycle CER reconstructed blind.
2. **Very tight cross-learner consistency** (0.14 pp overall; sets within ~0.5 pp). The unified skill is highly reproducible across independent learners.
3. **No within-hand learning curve on Sedley.** Both learners' letterform alphabets calibrated at set 1 and didn't drift. Forward CER is flat (~8–10%), with set 2 worse only because of one hard page. Decoding is solved early; residual error is *vocabulary*, which hand-accumulation can't fix. → Sedley is low-headroom (as the spec predicted); the learning-curve hypothesis needs a HARD hand (Saint, Brumwich) to test.
4. **Revision negligible on aggregate CER** — but conservative and honest: it fixed real misreadings where they existed (whore→sore, person→poyson, flannell, seed pearle) and refused to overwrite ambiguous strokes with sense-words. Few decoding errors to fix on an easy hand → little aggregate movement. Not a refutation of knowledge-driven revision; needs a hard hand to evaluate properly.
5. **Dominant error = modernization bias** (the project's known core risk): `vses`→uses, `vppon`→uppon, `vntill`→untill, `blood`→bloud, stripping apostrophes (`approv'd`→approved). #1 improvement target for the skill, despite the "preserve original spelling" instruction. Secondary: top-down word-substitution on hard/unfamiliar tokens (gutts→quills). Letterform/long-s confusion minimal — decoding is solid.

## Measurement caveats
- **Reference structural junk inflates raw CER uniformly:** reference files retain page numbers ("1."), recipe counters "(n)", `{page break}` lines, end-of-line hyphens that the transcriber omits. Absolute CER is inflated; relative (set/round) comparisons valid. Even inflated, ~9.5% is below the prior blind Sedley best (13.65%).
- **Reference fidelity is inconsistent** (sometimes archaic, sometimes normalized), which both inflates and confuses CER and penalizes faithful semi-diplomatic readings.

## Next steps
- Clean references (strip structural artifacts; check fidelity) — spec open-item #3.
- Strengthen anti-modernization in the skill.
- Run on a HARD hand (Saint/Brumwich) where decoding stays the bottleneck and the learning-curve + revision hypotheses have headroom.
- Robustness: long single-context runs drop (learner 3 socket, learner 1 stall) → move toward per-set agent invocations reading the persisted snapshot.
