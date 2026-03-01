# Blind Transcription Test — Run 8, Individual Pass

You are performing a **blind transcription** of early modern English manuscript pages using the **alphabet-first method**.

This is one of three independent passes. Your transcription will later be compared against two other independent transcriptions of the same pages. You must work entirely on your own — do not look for or reference any other transcriptions.

## What You Have Access To

- **5 manuscript images** (JPG files in `manuscripts/`)
- **A paleography guide** (`guide/paleography-guide.md`) — describes secretary hand letterforms, common abbreviations, and editorial conventions

You do **NOT** have access to any reference transcriptions, vocabulary lists, previous test results, or other passes. This is intentional.

## Workflow

For each manuscript, follow these two steps **in order**.

### Step 1: Build a Hand-Specific Alphabet

Before transcribing, study the manuscript image and create a letter-by-letter reference chart for this scribe's hand.

For each letter of the alphabet (a–z), document:
- **Letterform description**: How does this scribe form this letter?
- **Example words**: 2–4 words where this letter appears clearly
- **Confusion risks**: Which other letters could this be mistaken for in this hand?
- **Variants**: Does the scribe use more than one form?

Also document:
- Common combinations and ligatures (th, sh, ch, ff, -es graph, -er graph, etc.)
- A **ranked confusion risk summary** at the end, ordered highest to lowest risk

Save as `[manuscript]-alphabet.txt`

### Step 2: Transcribe

Using the alphabet from Step 1 and the paleography guide, transcribe the page.

Read **bottom-up**: identify pen strokes → match to letterforms → build words. Do NOT read top-down by guessing words from context.

**Rules:**
- Transcribe what you SEE, not what you think it should say
- Preserve original spelling — do not modernize
- Preserve original punctuation and capitalization
- Preserve original line breaks
- Expand abbreviations with supplied letters in *italics*
- Flag uncertain readings with [word?]
- Mark illegible text with [...] — do NOT guess or fabricate
- If most of a passage is illegible, mark the whole passage rather than reconstructing word by word

**Common pitfalls:**
- Doubled consonants (putt, itt, ytt, hott) — transcribe what you see, don't normalize
- Terminal 'e' (Coleworte, handefull, fundamente) — if the letterform is there, keep it
- Do NOT substitute familiar words for unfamiliar ones — early modern recipe books have specialized vocabulary that will look strange to modern readers
- An unfamiliar transcription is more likely correct than a familiar-sounding guess

Save as `[manuscript]-transcription.txt`

Include a "Confidence Notes" section at the end listing flagged readings.

## Manuscripts

Transcribe all five in the `manuscripts/` folder:
1. `henslow-ms688-page12.jpg`
2. `sedley-ms534-page13.jpg`
3. `bulkeley-ms169-page17.jpg`
4. `brumwich-ms160-page10.jpg`
5. `jane-jackson-ms373-page20.jpg`
