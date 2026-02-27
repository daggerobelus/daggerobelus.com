# Guided Transcription Test Results

Date: 2026-02-27
Method: Claude vision + paleography guide (ingest/references/paleography-guide.md)
Reference: FromThePage community transcriptions (compared word-by-word)

## Batch 1: Initial 5-Page Test

| Manuscript | Page | Words | Accuracy | Errors |
|---|---|---|---|---|
| Jane Jackson MS373 | 20 | 800 | 99.9% | 1 (confidence flag, not a real error) |
| Brumwich MS160 | 10 | 740 | 100.0% | 0 |
| Sedley MS534 | 13 | 396 | 99.5% | 2 |
| Bulkeley MS169 | 17 | 213 | 98.6% | 3 |
| Henslow MS688 | 12 | 163 | 95.7% | 6 |
| **Average** | | **2,312** | **~98.7%** | **12** |

## Observed Trends (Do Not Update Guide Yet — Need Larger Sample)

### 1. u/v Orthographic Choices
The guide says v is typically word-initial and u is medial, but the AI applies this rule too aggressively. Some scribes use u word-initially (e.g., "use" not "vse", "uppon" not "vppon"). The AI should transcribe the letterform it sees, not normalize.
- Henslow: 3 errors from this
- Bulkeley: 1 error from this

### 2. Modernization Bias
The AI "knows" modern English and leans toward familiar spellings. This directly contradicts the Folger principle to "forget how to spell."
- Henslow: "euenynde" read as "euenynge" (d misread as g because "evening" is familiar)
- Henslow: "voilett" read as "violett" (letter order transposed toward "violet")

### 3. Word Segmentation
When a scribe runs words together without a space, the AI tends to separate them.
- Henslow: "Takeone" read as "Take one"

### 4. Interlineal Insertions
The AI can miss text added above the line with caret marks.
- Sedley: "h^eales" read as "heales" (missed the caret notation)

### 5. Punctuation Ambiguity
Period vs. comma can be hard to distinguish in manuscript.
- Bulkeley: 1 punctuation error

## Notes

- All tests used pages with clearly-written hands. Harder tests (faded ink, compact hands, heavy abbreviation) still needed.
- Reference transcriptions are community-sourced from FromThePage, not triple-keyed scholarly editions. Some "errors" may be in the reference (e.g., Bulkeley "espetiallly" with 3 l's is likely a reference typo).
- An unguided baseline test (same pages without the paleography guide) would help measure the guide's specific contribution.

## IMPORTANT: Non-Blind Test Caveat

**These results are from a non-blind test** — the same agent that transcribed the pages also had access to the FromThePage reference transcriptions. This likely inflated the accuracy numbers.

Blind evaluation (where the transcription agent has NO access to the reference) was conducted on the same 5 manuscripts. Results were dramatically different:

- Henslow MS688: ~11-12% CER blind vs. 4.3% non-blind
- Sedley MS534: ~16-21% CER blind vs. 0.5% non-blind
- Jane Jackson and Brumwich: agent hallucinated entirely fabricated text (~95% CER)

An **alphabet-first method** (building a hand-specific letter reference before transcribing) improved Henslow to 6.12% CER — roughly 50% better than basic blind transcription.

See `blind-evaluation/blind-test-summary.md` for full blind evaluation results.
