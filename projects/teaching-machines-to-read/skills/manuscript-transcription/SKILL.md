---
name: manuscript-transcription
description: >
  Transcribe early modern English manuscript pages written in secretary hand.
  Use this skill whenever you are asked to transcribe a manuscript image, read
  handwriting from the 1500s-1700s, produce a semi-diplomatic transcription, or
  work with recipe books, letters, or other early modern documents. Also use when
  someone mentions paleography, secretary hand, or letterforms.
---

# Manuscript Transcription — Adaptive Method

You are transcribing an early modern English manuscript page written in secretary hand (roughly 1500–1700). This is a research transcription — the results will be evaluated against field-standard CER metrics and reviewed by paleography scholars.

This skill has two paths: **Standard** (for legible manuscripts) and **Scaffolded** (for degraded or difficult manuscripts). You choose which path to follow based on a triage assessment of the page.

## Your Materials

- **Manuscript image(s)** — the page(s) to transcribe
- **Paleography guide** — `ingest/references/paleography-guide.md` — secretary hand letterforms, abbreviations, and Folger semi-diplomatic conventions. Read this before starting.
- **Vocabulary reference** — `extracted/derived/vocab/vocab-reference.txt` — ~19,000 words attested in early modern recipe books. Used for verification.

If any of these are missing, ask before proceeding.

## Step 0: Triage

**Before transcribing anything, assess the page.** Scan the whole image and score each factor. Factors marked with **(×2)** are weighted double because they have the strongest effect on transcription accuracy.

| Factor | None (0) | Minor (1) | Moderate (2) | Severe (3) |
|---|---|---|---|---|
| **Physical damage** — water, mold, tears, foxing | None | Small areas affected | Significant areas obscured | Large areas destroyed or illegible |
| **Scan quality (×2)** — resolution, pages per image, lighting | Single page, high resolution, clear | Single page with slight blur or uneven lighting | 2-page spread OR moderate resolution loss | 2-page spread AND low resolution or poor lighting |
| **Hand density (×2)** — spacing between words and lines | Open, generous white space | Mostly open, a few tight areas | Tight in many areas, some lines overlap | Compressed throughout, little white space |
| **Multiple hands** — different scribes on the page | Single consistent hand | Minor shifts in style or size | Two distinguishable hands | Three or more hands, or dramatic shifts |
| **Ink quality** — fading, blotting, show-through | Dark, even, crisp | Slight fading or minor blotting | Noticeable fading in sections, some show-through | Heavy fading, blotting, or show-through throughout |
| **Hand quality** — how well-formed the letterforms are | Clear, careful, consistent forms | Mostly clear, occasional irregular forms | Frequently hasty or irregular, many ambiguous letters | Rough throughout, hard to distinguish individual letters |

**Scoring:** Add the scores. For factors marked (×2), multiply by 2 before adding.

**Maximum possible: 24** (6 factors, 2 weighted double, max 3 each = 4×3 + 2×6 = 24)

- **0–7 → Standard Path** (single pass with alphabet)
- **8+ → Scaffolded Path** (three-pass method)

Write down your assessment and total before proceeding. This is your first output — save it to `[manuscript]-triage.txt`.

---

## Standard Path (Score 0–7)

For legible manuscripts where the hand is clear enough to read on the first pass. The main job here is accuracy.

### Step 1: Build an Alphabet

Scan the whole page. Identify page numbers, headings, recipe boundaries, and the clearest text. Then build a hand-specific alphabet from the most legible words.

For each letter (a–z), document:
- How this scribe forms it (pen stroke direction, thick/thin, lifts)
- 2–4 clear example words
- Confusion risks (which letters look similar in this hand)
- Variants (e.g., long-s vs. round-s)

Also note ligatures (th, ff, -es graph, -er graph) and this scribe's specific habits.

**Calibrate the alphabet:** Pick 5 clear words from different parts of the page. Transcribe each one letter by letter using your alphabet. Check each against the vocab reference. If 3+ don't match any attested word, your alphabet has errors — revise before continuing.

**Note this scribe's orthographic habits:**
- u or v at word beginnings? ("vpon" or "upon"?)
- Doubled final consonants? ("itt" or "it"?)
- Terminal -e? ("fundamente" or "fundament"?)
- i or j? ("iuice" or "juice"?)

Every scribe is different. Do not carry habits from any previous manuscript.

**Save as:** `[manuscript]-alphabet.txt`

### Step 2: Transcribe

Work through the page using your alphabet. For each word:

1. Look at the pen strokes on the page
2. Match each stroke to a letterform in your alphabet
3. Assemble the letters into a word
4. If a word is unclear, check it against the vocab reference

**Confidence scale:**

| What you can see | What to write |
|---|---|
| Clear strokes, unambiguous reading | The word |
| Strokes visible but ambiguous (two possible readings) | `[word?]` |
| Some strokes visible, rest unclear | `[b....es]` (letters you can trace + dots) |
| No traceable strokes | `[...]` |

**The vocab list confirms readings — it does not generate them.** If you find yourself scanning the list for words that might fit, stop. Read the letterforms first, then check.

After completing the transcription, do one final check: read through and verify that the orthography is consistent with this scribe's habits.

→ **Skip to Output** below.

---

## Scaffolded Path (Score 8+)

For degraded or difficult manuscripts where the agent needs to separate "what I can see" from "what I think should be there." The main job here is calibration — knowing when to stop trying.

### Pass 1: Survey and Alphabet

**Task: learn this scribe's hand before reading the page.**

Same as Standard Path Step 1 — scan the page, build an alphabet, calibrate against vocab, note orthographic habits.

**Save as:** `[manuscript]-alphabet.txt`

### Pass 2: Skeleton

**Task: transcribe only what you can read from letterforms. Nothing else.**

Work through the page using your alphabet. For each word:

1. Look at the pen strokes on the page
2. Match each stroke to a letterform in your alphabet
3. Assemble the letters into a word

If you can trace every stroke → transcribe the word.
If you cannot trace the strokes → write `[...]` and move on.

**Do not reason from context in this pass.** Do not think about what word "makes sense." Do not fill in gaps based on what the recipe is about. This pass produces a gapped skeleton — headings, clear words, and honest gaps. That is exactly what it should look like.

**Confidence scale:**

| What you can see | What to write |
|---|---|
| Clear strokes, unambiguous reading | The word |
| Strokes visible but ambiguous (two possible readings) | `[word?]` |
| Some strokes visible, rest unclear | `[b....es]` (letters you can trace + dots) |
| No traceable strokes | `[...]` |
| Whole passage illegible | `[Passage illegible — ~N lines, reason]` |

### Pass 3: Fill and Verify

**Task: revisit the gaps. Use your alphabet and vocab reference together to attempt harder readings.**

Go back through every `[...]` gap and `[word?]` flag:

1. Look at the gap again. Can you see any partial strokes you missed?
2. Match visible strokes against your alphabet — do any letters become clear on a second look?
3. If you can propose a reading, check it against the vocab reference:
   - **On the list** → your confidence increases. Use `[word?]` if somewhat certain, or transcribe if now confident.
   - **Not on the list** → is there a plausible alternative (1–2 letters different) that IS on the list and that the strokes support? If so, consider it. If not, keep the gap.
4. If you still cannot read it, leave `[...]`. The gap is the correct transcription.

**The vocab list confirms readings — it does not generate them.** If you find yourself scanning the list for words that might fit, you have reversed the process.

After filling gaps, do one final check of the full transcription: read through and verify that the orthography is consistent with this scribe's habits.

→ **Continue to Output** below.

---

## Transcription Conventions

Follow Folger semi-diplomatic conventions (detailed in the paleography guide):

- Preserve original spelling exactly — "physicke" not "physic"
- Preserve original punctuation, capitalization, and line breaks
- Expand abbreviations with supplied letters in *italics*
- Preserve scribal errors — dittography, transpositions, false starts
- Keep the scribe's orthography — u/v, i/j, long-s, doubled consonants, terminal -e
- If the scribe wrote "vpon," transcribe "vpon." The scribe's spelling is the data.

## Output

Produce these files per page:

| File | Contents |
|------|----------|
| `[manuscript]-triage.txt` | Triage assessment: factor scores, total, path chosen |
| `[manuscript]-alphabet.txt` | Hand-specific alphabet with confusion risks and scribe's orthographic habits |
| `[manuscript]-transcription.txt` | **Plain transcription text only** — no headers, no metadata, no section markers |
| `[manuscript]-notes.txt` | Flagged readings: line number, your reading, why uncertain, vocab verification |

**The transcription file must contain ONLY the transcription.** No manuscript name, no date, no method notes. Just the text starting from the first line. The CER evaluation script compares character-by-character — any extra text inflates the error rate.
