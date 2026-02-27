# Blind Evaluation Test Results

Date: 2026-02-27
Method: Two-agent blind evaluation (transcription agent has no access to reference)

## Methodology

Previous tests had the same agent perform both transcription and evaluation, with access to the FromThePage reference transcriptions. This meant the transcription could be unconsciously influenced by the reference — like letting a student see the answer key during a test.

The blind evaluation separates these into two agents:
- **Agent 1 (Transcription):** Gets only the manuscript image + paleography guide. No access to reference text.
- **Agent 2 (Evaluation):** Gets the transcription + reference. Computes CER. Never sees the original image.

## Test Materials

Five manuscript pages from the initial 5-page test, reused for direct comparison:
- Jane Jackson MS373 page 20
- Brumwich MS160 page 10
- Sedley MS534 page 13
- Bulkeley MS169 page 17
- Henslow MS688 page 12

## Results Summary

### Run 1: Basic blind transcription

Guide: Original paleography guide (no anti-hallucination rules)

| Manuscript | CER | Notes |
|---|---|---|
| Jane Jackson MS373 | ~95.6% | HALLUCINATED — fabricated recipe text |
| Brumwich MS160 | ~96.1% | HALLUCINATED — fabricated recipe text |
| Sedley MS534 | ~15.8% | Correct page, many misreadings |
| Bulkeley MS169 | ~22.8% | Correct page, many misreadings |
| Henslow MS688 | ~11.3% | Best result, still above usable threshold |

Key finding: Without access to the reference, the agent hallucinated entire pages of plausible-sounding but fabricated recipe text for the two hardest manuscripts. The previous 0.45% CER on Sedley was inflated by the agent having access to the reference.

### Run 2: Updated guide with anti-hallucination rules

Guide: Added "Cardinal Rule: Never Fabricate Text" section, strengthened confidence flagging, added scribal error preservation examples.

| Manuscript | CER | vs Run 1 |
|---|---|---|
| Jane Jackson MS373 | ~95% | No change |
| Brumwich MS160 | ~93% | No change |
| Sedley MS534 | ~21% | Worse |
| Bulkeley MS169 | ~18% | Slightly better |
| Henslow MS688 | ~12% | About the same |

Key finding: Guide-level instructions alone did not fix hallucination or significantly improve accuracy. The problem is structural — the agent reads top-down (word patterns) rather than bottom-up (letterforms).

### Run 3: Alphabet-first method (Henslow only)

Three-agent workflow:
1. **Alphabet Builder** studies the hand and creates a letter-by-letter reference chart
2. **Transcriber** uses the alphabet + paleography guide to transcribe
3. **Evaluator** compares against reference

| Manuscript | CER | vs Run 2 |
|---|---|---|
| Henslow MS688 | 6.12% | ~50% reduction |

Error breakdown (58 edits / 948 characters):
- Letterform misreading: 31 edits (53%) — 3 word-level misreadings account for 19 of these
- Double-letter omission: 8 edits (14%) — systematic bias toward single consonants
- Capitalization: 5 edits (9%)
- Terminal 'e' omission: 4 edits (7%)
- Punctuation: 4 edits (7%)
- u/v convention: 3 edits (5%)
- Word segmentation: 1 edit (2%)

Key finding: The alphabet-first method forces bottom-up reading (letterforms first, then words) instead of top-down guessing. This cut the error rate roughly in half. Fixing 3 specific word misreadings would bring CER to ~4.1% (below the usable threshold).

## Comparison to Previous (Non-Blind) Results

| Method | Henslow CER | Sedley Full MS CER |
|---|---|---|
| Non-blind (agent sees reference) | 4.3% | 0.45% |
| Blind Run 1 | ~11.3% | ~15.8% |
| Blind Run 2 | ~12% | ~21% |
| Blind Run 3 (alphabet method) | 6.12% | not tested yet |

The non-blind results were inflated. The blind evaluation gives an honest assessment of the pipeline's actual capability.

## Next Steps

1. Test alphabet method on harder manuscripts (Sedley, Bulkeley)
2. Address systematic doubled-consonant bias in the guide
3. Explore multi-pass transcription (multiple reads of the same page)
4. Consider image preprocessing (contrast enhancement, zoomed sections)
5. The hallucination problem on illegible manuscripts remains unsolved — these need human transcription or a different approach (e.g., fine-tuned TrOCR)
