# Run 9: Self-Taught Method — Results

Date: 2026-03-25
Method: Self-taught paleography (agent learns from paired examples, no external guide)
Test page: Henslow MS688 page 12

## Experiment Design

### Question
Can an AI agent learn to read early modern handwriting by studying paired manuscript images + transcriptions, without any external paleography guide?

### Method
1. **Learning agent** studies N manuscript pages paired with their correct transcriptions. No paleography guide, no vocab list, no Folger conventions. Writes its own guide.
2. **Transcription agents** (5 per run) transcribe Henslow using only the self-taught guide.
3. CER computed against FromThePage reference.

### Variables Tested
- Number of training pages: 1, 3, 5, 10
- Reflection step: agents given self-taught guide + paleography guide + vocab list, write a reflection before transcribing

### Training Materials
- **1-page:** Sedley MS534
- **3-page:** Brumwich MS160, Bulkeley MS169, Sedley MS534
- **5-page:** Above + Ayscough MS1026, RCP MS502
- **10-page:** Above + RCP MS504, Fanshawe MS7113, St. John MS4338, Gibson MS311 (pages 20 & 40)

All training manuscripts are from the early modern period (1580–1692), fully transcribed on FromThePage, and use different scribal hands.

### Test Isolation
Each agent ran in a completely clean folder containing ONLY its authorized materials. No shared output folders, no access to other agents' work. Earlier runs using a shared output folder produced inflated results (see Contamination Note below).

## Results (Clean Runs)

### Learning Curve — Self-Taught Guide Only

| Training Pages | Agent 1 | Agent 2 | Agent 3 | Agent 4 | Agent 5 | Best | Median | Worst | Spread |
|---|---|---|---|---|---|---|---|---|---|
| 1 page | 7.28% | 7.91% | 7.17% | 7.59% | 7.91% | 7.17% | 7.59% | 7.91% | 0.74 |
| 3 pages | 5.06% | 6.01% | 6.86% | 7.17% | 6.86% | 5.06% | 6.86% | 7.17% | 2.11 |
| 5 pages | 6.01% | 5.17% | 6.43% | 6.43% | 7.17% | 5.17% | 6.43% | 7.17% | 2.00 |
| 10 pages | 6.86% | 6.01% | 5.80% | 6.33% | 6.54% | 5.80% | 6.33% | 6.86% | 1.06 |

### Reflection Method (5-page guide + paleography guide + vocab, with written reflection before transcribing)

| Agent 1 | Agent 2 | Agent 3 | Agent 4 | Agent 5 | Best | Median | Worst | Spread |
|---|---|---|---|---|---|---|---|---|
| 6.43% | 5.59% | 5.70% | 5.80% | 5.70% | 5.59% | 5.70% | 6.43% | 0.84 |

### Comparison to Previous Runs

| Method | Best CER | Median CER |
|---|---|---|
| Run 6 (alphabet-first + vocab) | **3.80%** | — |
| Run 4 (alphabet-first) | 4.96% | — |
| Run 9: 3-page self-taught | 5.06% | 6.86% |
| Run 9: 5-page self-taught | 5.17% | 6.43% |
| **Run 9: Reflection** | **5.59%** | **5.70%** |
| Run 9: 10-page self-taught | 5.80% | 6.33% |
| Run 3 (alphabet-first, first attempt) | 6.12% | — |
| Run 9: 1-page self-taught | 7.17% | 7.59% |
| Run 1 (basic blind) | ~11.3% | — |

## Key Findings

1. **The learning curve is real.** More training pages improves performance: 1 page (7.59% median) → 3 pages (6.86%) → 5 pages (6.43%) → 10 pages (6.33%). Returns diminish after 5 pages.

2. **Reflection improves consistency, not just accuracy.** The reflection method has the best median (5.70%) and the tightest spread (0.84 points). Standard self-taught runs have 1–2 point spreads. Reflection makes agents more reliable.

3. **Consistency and accuracy are separate problems.** The best single-agent result (3-page, 5.06%) came from a run with high variance (2.11 spread). The reflection method's best (5.59%) is worse, but its worst (6.43%) is much better than other runs' worst cases. Different interventions target different problems.

4. **The self-taught method discovers core paleography rules independently.** All guides independently identified: u/v interchange, long-s vs f, the minim problem, the "ff" convention, terminal -e, and recipe-specific vocabulary patterns.

5. **Post-hoc revision doesn't work.** Confirmed again: giving agents better tools AFTER they've transcribed doesn't meaningfully improve results. Agents rubber-stamp their own work. (This was also shown in Run 5.)

6. **The alphabet-first method still leads.** Run 6's 3.80% remains the best result. The key advantage of alphabet-first is forcing the agent to study THIS SPECIFIC scribe's hand before transcribing, rather than learning general early modern conventions from other scribes.

## Contamination Note

Early runs in this experiment used a shared output folder (`~/Desktop/blind-test-self-taught/output/`) where all agents saved their work. Later agents could see previous agents' transcriptions, inflating results by 1–2 percentage points. The contaminated results showed:
- 5-page best: 3.80% (contaminated) vs. 5.17% (clean)
- 10-page best: 4.22% (contaminated) vs. 5.80% (clean)

**All results in this document are from clean, isolated runs.** The contamination was caught during the session and the isolation rule has been added to the project CLAUDE.md.

## Lessons for Test Design

- **Each agent must run in a completely isolated folder** containing only its authorized materials
- **No shared output folders** — agents browse their environment and can be influenced by other transcriptions
- **Pre-create output files** if agents need write permissions to new directories
- **Post-hoc revision is a dead end** — don't keep testing variations of it
- **Run 5 agents per condition** to measure both accuracy (best) and consistency (spread)

## Run 10: Error Analysis Protocol (Sedley MS534)

The error analysis experiment was completed in the same session. An Error Analysis Agent studied the 5 Henslow transcriptions from the 5-page run against the reference, identified systematic error patterns, and wrote a revised protocol. The protocol was then tested on Sedley MS534 — a different manuscript the protocol had never seen — to verify generalization.

### Sedley Results

| Method | Best | Median | Worst | Spread |
|---|---|---|---|---|
| Baseline (self-taught only) | 14.18% | 14.86% | 15.54% | 1.36 |
| **Error protocol** | **13.65%** | **13.89%** | 15.93% | 2.28 |
| Run 4 alphabet-first (previous best) | 15.13% | — | — | — |

Key findings: The error protocol improved accuracy (13.65% vs 14.18% best, 13.89% vs 14.86% median). Both self-taught methods beat the previous Sedley best (Run 4, 15.13%). The protocol generalized from Henslow to Sedley despite being built from Henslow-specific errors. Consistency was slightly worse (2.28 vs 1.36 spread).

Full results: `~/Desktop/run-10-error-protocol-results.docx.md`

## Next Steps

1. **Iterative error analysis:** Run the error analysis loop again — analyze Sedley errors, update the protocol, test on Bulkeley or Brumwich. Each cycle should accumulate lessons. The question is whether the protocol converges toward a stable set of rules or keeps discovering new failure modes.

2. **Same-agent learning:** Test whether an agent that writes its own guide and then uses it (same context) outperforms one that reads someone else's guide. The "taking your own notes" hypothesis.

3. **Combine self-taught with alphabet-first:** Use the self-taught guide as general background, then still build a page-specific alphabet (Run 6's key ingredient). This combines general knowledge with scribe-specific analysis.

4. **Scale to full manuscripts:** Current results are single pages. Test whether the methodology holds across multiple pages of the same manuscript, and whether a protocol trained on early pages improves performance on later pages.
