# Blind Transcription Test — Run 8, Reconciliation

You are the reconciliation agent for a triple-pass blind transcription test. Three independent agents have each transcribed the same five manuscript pages without seeing each other's work. Your job is to produce a single consensus transcription for each manuscript.

## What You Have Access To

- **Three independent transcriptions per manuscript** (in `pass-1/`, `pass-2/`, `pass-3/`)
- **A vocabulary reference** (`guide/vocab-reference.txt`) — ~19,000 words attested in early modern recipe books. Use this only in the final verification step, not during reconciliation.

You do **NOT** have access to the original manuscript images or any reference transcriptions.

## Workflow

### Step 1: Reconcile Each Manuscript

For each of the five manuscripts, compare the three transcriptions line by line, word by word.

**Majority rule:** Where two or three passes agree on a word, that is the consensus reading.

**Disagreements:** Where all three passes differ:
- If two readings are similar and one is very different, favor the more similar pair
- If all three are plausible, flag the word for review: [word1/word2/word3?]
- If two or more passes marked a word as [...] (illegible), the consensus is [...]
- If one pass has [...] but two passes have a reading, use the reading

**Line structure:** Use the line breaks from whichever pass has the most consistent lineation. If all three differ, use the structure that preserves the most detail.

For each manuscript, save:
- `[manuscript]-consensus.txt` — the reconciled transcription
- `[manuscript]-reconciliation-notes.txt` — a record of every disagreement between the three passes and how you resolved it

### Step 2: Vocabulary Verification (Final Step)

**Only after completing all five consensus transcriptions**, open `guide/vocab-reference.txt` and check the consensus against it.

Focus on:
- Words where the three passes disagreed (your flagged items)
- Words that look unfamiliar or unusual
- Do NOT re-check words where all three passes agreed — those readings are already strong

Rules for vocab verification:
- The vocab list confirms readings, it does not generate them
- If the consensus reading is on the list, confidence increases
- If the consensus reading is NOT on the list, check if a close alternative is — but only adopt it if it's consistent with the majority of the three passes
- Never override a strong three-way agreement based on the vocab list

Save the final version as `[manuscript]-final.txt` if vocab verification changed anything. If no changes, the consensus file is the final version.

## Output Summary

At the end, write a summary file `reconciliation-summary.txt` that includes:
- For each manuscript: number of agreements (3-way, 2-way) and disagreements
- Total words where vocab verification changed the reading
- Your assessment of which manuscripts had the most consistent readings across passes and which had the most variation

## Manuscripts

Process all five:
1. Henslow MS688
2. Sedley MS534
3. Bulkeley MS169
4. Brumwich MS160
5. Jane Jackson MS373
