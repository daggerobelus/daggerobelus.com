# Blind Transcription Test — Alphabet-First Method

## Overview

You are performing a **blind transcription** of early modern English manuscript pages using the **alphabet-first method**. This is a three-step process designed to force bottom-up reading (identifying individual letterforms first, then assembling words) rather than top-down guessing (predicting words from context).

You have access to:

- **5 manuscript images** (JPG files in the `manuscripts/` folder)
- **A paleography guide** (`guide/paleography-guide.md`) that describes secretary hand letterforms, common abbreviations, and editorial conventions
- **A vocabulary reference** (`guide/vocab-reference.txt`) containing ~19,000 words attested in early modern recipe books, printed herbals, and EMROC transcriptions — use this to verify your readings (see Step 2b below)

You do **NOT** have access to any reference transcriptions, previous test results, or evaluation reports. This is intentional — your transcription must be based solely on what you can read in the manuscript images.

---

## The Three-Step Workflow

Each manuscript page must go through all three steps **in order**. Do not skip steps.

### Step 1: Build a Hand-Specific Alphabet

Before transcribing anything, study the manuscript image and create a **letter-by-letter reference chart** for this specific scribe's hand.

For each letter of the alphabet (a–z), document:

- **Letterform description**: How does this scribe form this letter? Describe the pen strokes.
- **Example words**: List 2–4 words on the page where this letter appears clearly, with line references.
- **Confusion risks**: Which other letters could this one be mistaken for in this specific hand?
- **Variants**: Does the scribe use more than one form of this letter (e.g., long-s vs. round-s)?

If a letter does not appear on the page, note that.

Also document:

- **Common combinations and ligatures** (th, sh, ch, ff, -es graph, -er graph, etc.)
- **Distinctive features of this hand** (decorative capitals, spacing habits, ink characteristics, etc.)

#### Confusion Risk Ranking

At the end of the alphabet chart, include a **ranked summary of confusion risks** for this hand, ordered from highest to lowest risk. For each entry, explain:

- Which letters are being confused
- Why they look similar in this hand specifically
- What distinguishing features (if any) can help tell them apart

This ranking helps the transcriber know where to pay the most careful attention.

#### Save the alphabet as: `[manuscript]-alphabet.txt`

### Step 2: Transcribe the Page

Using the hand-specific alphabet from Step 1 **and** the general paleography guide, produce a **semi-diplomatic transcription** of the manuscript page.

The alphabet chart is your primary reference for this specific scribe's letterforms. The paleography guide provides general background on secretary hand conventions.

**How to use the alphabet during transcription:**

- For each word, identify individual letterforms by cross-referencing against the alphabet chart
- When you encounter a letter sequence that matches a high-risk confusion pair from the ranking, slow down and compare carefully against the examples in the alphabet
- Read bottom-up: identify the **pen strokes** you see, match them to letterforms, then assemble the word — do NOT start with a guess about what word it might be

#### Transcription Rules

Follow the Folger semi-diplomatic conventions described in the paleography guide. The key rules:

- **Transcribe what you SEE, not what you think it should say**
- Preserve original spelling exactly — do not modernize
- Preserve original punctuation and capitalization
- Preserve original lineation (line breaks where the scribe made them)
- Expand abbreviations with supplied letters in italics (use *italics* in markdown)
- Flag uncertain readings with `[word?]` notation
- Mark illegible text with `[...]` — do NOT guess

#### Common Pitfalls to Avoid

These are systematic errors observed in previous blind transcriptions. Watch out for them:

1. **Doubled consonants**: Early modern scribes frequently doubled consonants (putt, itt, ytt, hott). Do NOT normalize these to single consonants. If you see two pen strokes, transcribe two letters.

2. **Terminal 'e'**: Many early modern words end in 'e' that modern English has dropped (Coleworte, handefull, fundamente). If the letterform is there, transcribe it — even if the modern spelling omits it.

3. **Context-based word substitution**: Do NOT substitute a familiar word for what you see. If the letterforms spell out an unfamiliar word, transcribe the unfamiliar word. Early modern recipe books contain many plant names, medical terms, and archaic words that will look strange to a modern reader. An unfamiliar-looking transcription is more likely to be correct than a familiar-looking guess.

4. **Hallucination**: If you cannot read a passage, mark it `[...]`. Do NOT fabricate plausible-sounding recipe text. A page full of `[...]` gaps is more valuable than a page full of invented text.

### Step 2b: Verify Against Vocabulary Reference

After completing your first-pass transcription (Step 2), go back through it and check each unfamiliar or uncertain word against the vocabulary reference file (`guide/vocab-reference.txt`). This file contains ~19,000 words that actually appear in human-transcribed early modern recipe books, printed herbals (Gerard 1597, Culpeper 1652), and EMROC triple-keyed transcriptions.

**How to use the vocabulary reference:**

1. **Read letterforms first, verify second.** Always complete your letterform-based reading before checking the vocab list. The list is a verification tool, not a prediction tool — it confirms readings, it does not generate them.

2. **If your reading appears on the list**, your confidence in that reading increases. The word is attested in other early modern recipe manuscripts.

3. **If your reading does NOT appear on the list**, do one of the following:
   - **Re-examine the letterforms.** Go back to the alphabet chart and check each letter again. Is there a plausible alternative reading where one or two letters are different? If that alternative reading IS on the vocab list, it may be the correct reading — but only if the letterforms genuinely support it.
   - **Keep your original reading.** The vocab list does not contain every word. The manuscript may use a spelling or term that doesn't appear in the reference set. A word not on the list is not automatically wrong.

4. **Never let the vocab list override clear letterforms.** If you can clearly see the pen strokes and they spell a word not on the list, transcribe what you see. The list is evidence, not authority.

5. **In your Confidence Notes**, mention when the vocab list confirmed or challenged a reading. For example: "Read 'calcinated' — confirmed in vocab reference (attested in 6+ manuscripts)."

#### Output Format

For each page, produce:
- A header with the manuscript name and page number (from the filename)
- The transcription, preserving original spelling, punctuation, capitalization, and lineation
- A "Confidence Notes" section listing any flagged readings and why they are uncertain

#### Save the transcription as: `[manuscript]-transcription.txt`

### Step 3: Evaluation (Separate Agent)

**You do NOT perform this step.** A separate evaluation agent, with no access to the manuscript images, will compare your transcription against a reference and compute the Character Error Rate (CER). This separation ensures the evaluation is unbiased.

---

## File Naming

For each manuscript, you will produce two files:

| File | Contents |
|------|----------|
| `[manuscript]-alphabet.txt` | Hand-specific letter chart with confusion risk ranking |
| `[manuscript]-transcription.txt` | Semi-diplomatic transcription with confidence notes |

Use the manuscript name from the image filename (e.g., `jane-jackson-ms373-page20-alphabet.txt`).

---

## Order of Operations

Process the manuscripts in any order, but for each one, always complete the alphabet (Step 1) before starting the transcription (Step 2). Never transcribe without building the alphabet first — that is the whole point of this method.
