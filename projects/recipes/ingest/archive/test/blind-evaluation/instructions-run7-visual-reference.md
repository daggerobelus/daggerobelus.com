# Blind Transcription Test — Run 7 Instructions

You are performing a **blind transcription** of early modern English manuscript pages.

## What You Have Access To

- **5 manuscript images** (JPG files in `manuscripts/`)
- **A paleography guide** (`guide/paleography-guide.md`) — describes secretary hand letterforms, common abbreviations, and editorial conventions
- **Visual reference charts** (`guide/secretary-hand-reference/`) — Folger Shakespeare Library charts showing:
  - `minuscule-alphabet.jpg` — Multiple variant forms for every lowercase secretary hand letter (a–z)
  - `majuscule-alphabet.jpg` — Multiple variant forms for every uppercase/capital letter (A–Z)
  - `abbreviations-1.jpg` and `abbreviations-2.jpg` — Common abbreviations with real manuscript image examples
  - `special-graphs-1.jpg` and `special-graphs-2.jpg` — Special shorthand marks (-es graph, -er graph, -ur graph, "special" p, thorn, etc.) with real manuscript image examples
- **A vocabulary reference** (`guide/vocab-reference.txt`) — ~19,000 words attested in early modern recipe books. **Only use this in the final step.**

You do **NOT** have access to any reference transcriptions or previous test results. This is intentional — your transcription must be based solely on what you can read in the manuscript images.

## Workflow

Follow these steps **in order** for each manuscript. Do not skip steps or combine them.

### Step 1: Study the General Secretary Hand Reference

Before touching any manuscript, study the visual reference charts in `guide/secretary-hand-reference/`:

1. Open `minuscule-alphabet.jpg` and `majuscule-alphabet.jpg`. Study the variant forms for every letter. Pay special attention to letters that have forms very different from modern handwriting (e, c, r, s, h, d, k, etc.). Note which letters have forms that could be confused with each other.
2. Open `abbreviations-1.jpg` and `abbreviations-2.jpg`. Study the manuscript image examples next to each abbreviation. Note what these abbreviations look like in real handwriting — not just the text description, but the actual visual form.
3. Open `special-graphs-1.jpg` and `special-graphs-2.jpg`. Study the -es graph, -er graph, -ur graph, "special" p, thorn, and other shorthand marks. Again, focus on the manuscript image examples — learn what these marks look like in real ink.

Also read `guide/paleography-guide.md` for the text descriptions and editorial conventions.

**You only need to do Step 1 once** — the general reference applies to all five manuscripts.

### Step 2: Build a Hand-Specific Alphabet

For each manuscript image, **before transcribing**, study the specific scribe's hand:

1. Open the manuscript image
2. Working through the alphabet (a, b, c, d, ...), find clear examples of each letter in the manuscript
3. For each letter, note:
   - What it looks like in this scribe's hand
   - Which variant form from the Folger reference chart it most closely matches
   - Which other letters it could be confused with in this hand
4. Note any abbreviations or special graphs you can see in the manuscript, matching them to the visual examples from Step 1
5. Save this alphabet as `[manuscript]-alphabet.txt`

**Do NOT transcribe yet.** This step is only for studying the hand.

### Step 3: Transcribe

Now transcribe the manuscript page using:
- Your hand-specific alphabet from Step 2
- The general Folger visual reference from Step 1
- The editorial conventions in `guide/paleography-guide.md`

Read **bottom-up**: identify individual pen strokes → recognize letterforms → build words. Do NOT read top-down (guessing words from context).

**Critical rules:**
- Transcribe what you SEE, not what you think it should say
- Preserve original spelling — do not modernize
- Preserve original punctuation and capitalization
- Preserve original line breaks
- Expand abbreviations with supplied letters in *italics*
- Flag uncertain readings with [word?] notation
- If you cannot read it, mark it as [...] — do NOT guess
- If most of a passage is illegible, mark the whole passage as illegible rather than reconstructing word by word

Save the transcription as `[manuscript]-transcription.txt`.

### Step 4: Vocabulary Verification (Final Step Only)

**Only after completing the transcription in Step 3**, open `guide/vocab-reference.txt` and check your uncertain or unfamiliar readings against it.

- For each word you flagged with [word?], check if a similar word appears in the vocab list
- For words that look unusual, check if they are attested early modern forms
- If the vocab list confirms a reading you were uncertain about, you may upgrade your confidence
- If the vocab list suggests a different word that better matches the letterforms you see, you may revise — but **only if the letterforms support it**
- Clear letterforms always override the vocab list

**Do NOT use the vocab list during Steps 1–3.** It is a verification tool for the end of the process, not a reading aid.

Save the final (post-verification) transcription as `[manuscript]-transcription-final.txt` if you made any changes. If no changes, the Step 3 transcription is your final version.

## Output Format

For each manuscript, produce:
- `[manuscript]-alphabet.txt` — the hand-specific alphabet (Step 2)
- `[manuscript]-transcription.txt` — the transcription (Step 3)
- `[manuscript]-transcription-final.txt` — only if vocab verification changed anything (Step 4)
- Include a "Confidence Notes" section at the end of each transcription listing any flagged readings

## Manuscript Files

Transcribe all five manuscripts in the `manuscripts/` folder:
1. `henslow-ms688-page12.jpg`
2. `sedley-ms534-page13.jpg`
3. `bulkeley-ms169-page17.jpg`
4. `brumwich-ms160-page10.jpg`
5. `jane-jackson-ms373-page20.jpg`
