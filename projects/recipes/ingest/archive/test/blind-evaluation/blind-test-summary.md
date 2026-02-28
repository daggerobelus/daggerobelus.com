# Blind Evaluation Test Results

Date: 2026-02-27
Method: Multi-agent blind evaluation with progressive methodology refinement

## Methodology

Previous tests had the same agent perform both transcription and evaluation, with access to the FromThePage reference transcriptions. This meant the transcription could be unconsciously influenced by the reference — like letting a student see the answer key during a test. The non-blind full Sedley test reported 0.45% CER, which turned out to be dramatically inflated.

The blind evaluation separates transcription and evaluation into agents with no shared context:
- **Transcription agent:** Receives only the manuscript image + paleography guide. No access to reference text.
- **Evaluation agent:** Receives the transcription + reference. Computes CER. Never sees the original image.

## Test Materials

Five manuscript pages, reused across all runs for direct comparison:
- Jane Jackson MS373 page 20 — very difficult (water damage + compact hand)
- Brumwich MS160 page 10 — difficult (small, dense hand, two-page spread)
- Sedley MS534 page 13 — moderate (clear italic hand)
- Bulkeley MS169 page 17 — moderate (herbal text with specialized vocabulary)
- Henslow MS688 page 12 — easiest (large, neat secretary hand)

## Results Summary

| Manuscript | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Run 6 |
|---|---|---|---|---|---|---|
| Henslow MS688 | ~11.3% | ~12% | 6.12% | 4.96% | 5.38% | **3.80%** |
| Sedley MS534 | ~15.8% | ~21% | N/A | 15.13% | 16.55% | 16.96% |
| Bulkeley MS169 | ~22.8% | ~18% | N/A | 18.70% | 20.90% | **16.21%** |
| Brumwich MS160 | ~96.1% | ~93% | N/A | 9.30% | 50.62% | 69.29% |
| Jane Jackson MS373 | ~95.6% | ~95% | N/A | 77.41% | 46.85% | 80.62% |

Benchmarks:
- < 1% CER = very good
- < 5% CER = usable for most research purposes
- ~3% CER = Transkribus Egerton model (best existing for English secretary hand)

---

## Run-by-Run Details

### Run 1: Basic blind transcription
- **Date:** 2026-02-27
- **Method:** Single agent with original paleography guide, no special methodology
- **Instructions:** Basic blind transcription instructions (`instructions.md`)
- **Key finding:** Without access to the reference, the agent hallucinated entire pages of fabricated recipe text for the two hardest manuscripts (Jane Jackson ~95.6%, Brumwich ~96.1%). Even legible manuscripts had 11-23% CER. The previous non-blind 0.45% CER on Sedley was exposed as inflated.
- **Files:** `run-1/` and `run-2/` folders

### Run 2: Updated guide with anti-hallucination rules
- **Date:** 2026-02-27
- **Method:** Same as Run 1 but with updated paleography guide adding "Cardinal Rule: Never Fabricate Text" section, strengthened confidence flagging, scribal error preservation examples
- **Key finding:** Guide-level instructions alone did not fix hallucination or significantly improve accuracy. The problem is structural — the agent reads top-down (word patterns) rather than bottom-up (letterforms). Changing instructions without changing the process doesn't work.
- **Files:** `run-2/` folder

### Run 3: Alphabet-first method (Henslow only)
- **Date:** 2026-02-27
- **Method:** Three-agent workflow: (1) Alphabet Builder studies the hand and creates a letter-by-letter reference chart, (2) Transcriber uses the alphabet + paleography guide, (3) Evaluator compares against reference
- **Key finding:** The alphabet-first method forces bottom-up reading (letterforms first, then words) instead of top-down guessing. This cut the error rate roughly in half on Henslow (11.3% to 6.12%). Based on how human paleographers are trained: study the hand first, then transcribe.
- **Important note:** The instructions for the alphabet-first method were given verbally in conversation and NOT saved. This was corrected in Run 4 by writing formal instructions.
- **Files:** `run-3-alphabet/` folder

### Run 4: Alphabet-first method (all 5 manuscripts, formalized instructions)
- **Date:** 2026-02-27
- **Method:** Same alphabet-first workflow as Run 3, but with formal written instructions (`instructions.md`) that documented the full methodology including confusion risk ranking. Test run isolated on Desktop to prevent agent from seeing reference materials.
- **Key findings:**
  - Henslow reached **4.96% CER** — crossed the <5% usable threshold
  - Brumwich went from ~96% (hallucinated) to **9.30%** — the most dramatic improvement
  - Jane Jackson and Brumwich no longer hallucinated; agent used `[...]` for illegible text instead
  - Sedley (15.13%) and Bulkeley (18.70%) improved but remained above usable threshold
  - Formalized instructions actually improved on the ad-hoc Run 3 result for Henslow
  - Remaining errors dominated by whole-word misreadings — agent substituting familiar words for unfamiliar vocabulary (e.g., "and buglosse" for "langdebeeffe", "seirced" for "calcinated")
- **Files:** `run-4-alphabet/` folder

### Run 5: Stronger instructions + review agent
- **Date:** 2026-02-27
- **Method:** Updated instructions with prominent "Core Principle: Read Letters Not Words" section + a separate review agent for manuscripts with >20% flagged words. Review agent re-examined flagged passages letter by letter with fresh context.
- **Key findings:**
  - No meaningful improvement on the three readable manuscripts (Henslow 5.38%, Sedley 16.55%, Bulkeley 20.90%)
  - Confirmed the pattern from Runs 1 vs 2: instruction changes alone don't move the needle
  - Review agent was effective at resolving over-flagging (Brumwich: 70.3% flags down to 13.2%; Jane Jackson: 62.4% down to 11.0%) but could not improve fundamental reading accuracy
  - The bottleneck is letterform recognition, not confidence calibration
  - **Decision: Reverted to Run 4 instructions** as the baseline, since Run 5 instruction changes didn't help
- **Files:** `run-5-alphabet/` folder

### Run 6: Alphabet-first method + vocabulary verification
- **Date:** 2026-02-27
- **Method:** Run 4 instructions (alphabet-first) plus a new Step 2b: after transcribing, agent verifies readings against a vocabulary reference of ~19,000 words attested in early modern recipe books. The vocab list was built from 38 FromThePage transcriptions, 3 EMROC triple-keyed transcriptions, and 2 printed herbals (Gerard 1597, Culpeper 1652) — totaling 1.68 million words across 40 sources.
- **Key findings:**
  - Henslow reached **3.80% CER** — best result across all runs, approaching the Transkribus Egerton benchmark (~3%)
  - Bulkeley improved to **16.21%** — best result for this manuscript, down 2.5 points from Run 4
  - Sedley flat at ~16% — errors there are whole-word hallucinations that the vocab list can't catch
  - Brumwich and Jane Jackson worse — the vocab list made the agent more conservative, marking more text `[...]` rather than guessing. Better scholarship but worse CER scores.
  - The vocab list genuinely helps on legible manuscripts. For difficult manuscripts, the bottleneck is image resolution and hand legibility, not vocabulary.
  - Vocab list caught specific corrections: "Sallanders" corrected to "Sallendine" (celandine) on Sedley
- **Files:** `run-6-alphabet-vocab/` folder
- **Vocab list:** `extracted/derived/vocab/`

---

## Key Lessons Learned

1. **Non-blind testing produces inflated results.** The 0.45% CER from the non-blind Sedley test was meaningless. Always use blind evaluation.

2. **Instruction changes alone don't improve accuracy.** Runs 1→2 and 4→5 both showed that telling the agent to "try harder" or "read letterforms more carefully" has negligible effect. Structural changes to the process are what matter.

3. **The alphabet-first method is the single biggest improvement.** It forces bottom-up reading, which is how human paleographers actually work. This was discovered in Run 3 and formalized in Run 4.

4. **Vocabulary verification helps on legible manuscripts.** The vocab list improved Henslow from 4.96% to 3.80% and Bulkeley from 18.70% to 16.21%. It works by giving the agent a way to catch its own misreadings.

5. **Image resolution is the hard ceiling for difficult manuscripts.** No amount of methodology will fix text where the pen strokes are physically indistinguishable. Brumwich and Jane Jackson need either higher-resolution images or human paleographic expertise.

6. **Honest gaps are better than plausible fiction.** The shift from fabricated text (~96% CER) to `[...]` markers is a fundamental improvement in reliability, even though it produces worse CER numbers.

## Current Best Results

| Manuscript | Best CER | Best Run | Status |
|---|---|---|---|
| Henslow MS688 | **3.80%** | Run 6 | Near Transkribus benchmark, usable for research |
| Sedley MS534 | **15.13%** | Run 4 | Above usable threshold, needs work |
| Bulkeley MS169 | **16.21%** | Run 6 | Above usable threshold, needs work |
| Brumwich MS160 | **9.30%** | Run 4 | Above usable threshold, image resolution limited |
| Jane Jackson MS373 | **46.85%** | Run 5 | Water damage, needs human transcription |

## Next Steps

1. **Expand testing to more manuscript pages** — Current results are based on 1 page per manuscript. Need to test across multiple pages to confirm the methodology holds.
2. **Test with higher-resolution images** — Brumwich's small hand might be readable at higher resolution. Check if better images are available from Wellcome Collection.
3. **Explore multi-pass transcription** — Multiple independent reads of the same page, compared for consistency.
4. **Fine-tune TrOCR** — The long-term goal remains an open-source model trained on the FromThePage paired data. The vocab list and transcription pipeline developed here will feed into that work.
5. **Apply for computing resources** — CUNY HPCC account, Google Colab student access, Provost's Digital Innovation Grant for cloud GPU time.

## Comparison to Non-Blind Results

| Method | Henslow CER | Sedley Full MS CER |
|---|---|---|
| Non-blind (agent sees reference) | 4.3% | 0.45% |
| Blind Run 1 | ~11.3% | ~15.8% |
| Blind Run 4 (alphabet method) | 4.96% | 15.13% |
| Blind Run 6 (alphabet + vocab) | 3.80% | 16.96% |

The non-blind results were inflated. The blind evaluation gives an honest assessment of the pipeline's actual capability.
