---
name: manuscript-transcription
description: >
  Transcribe early modern English manuscript pages written in secretary hand.
  Use this skill whenever you are asked to transcribe a manuscript image, read
  handwriting from the 1500s-1700s, produce a semi-diplomatic transcription, or
  work with recipe books, letters, or other early modern documents. Also use when
  someone mentions paleography, secretary hand, or letterforms.
---

# Manuscript Transcription — Alphabet-First Method

## Research Context

This transcription is part of a digital humanities research project investigating how AI agents learn to read early modern handwriting. The results will be presented to scholars in English literature, digital humanities, and paleography. Every transcription you produce may be compared against Transkribus benchmarks and evaluated using field-standard CER metrics (computed by `jiwer`, the same library used in ICDAR HTR competitions).

This means: **do not cut corners.** Do not hand-roll approximations when the skill gives you a method. Do not skip steps to save time. Do not use general knowledge of English to fill in what you can't read. The people reviewing this work are experts who will immediately spot modernization, hallucination, or lazy heuristics. An honest gap (`[...]`) is respected; a confident wrong answer is not.

## The Method

You are transcribing an early modern English manuscript page written in secretary hand (roughly 1500–1700). This method forces you to read **bottom-up** — identifying individual pen strokes and letterforms before assembling words — rather than top-down guessing from context.

Top-down reading is the single biggest source of error. When you guess what a word "should be" based on context, you silently replace the historical record with modern English. The alphabet-first method prevents this.

## Your Materials

You should have access to:

- **Manuscript image(s)** — the page(s) to transcribe
- **Paleography guide** — `ingest/references/paleography-guide.md` describes secretary hand letterforms, common abbreviations, and Folger semi-diplomatic editorial conventions. Read this before starting.
- **Vocabulary reference** — `extracted/derived/vocab/vocab-reference.txt` contains ~19,000 words attested in early modern recipe books, printed herbals, and EMROC transcriptions. Used in Step 3 for verification only.

If any of these are missing, ask before proceeding. Do not attempt a transcription without the paleography guide.

## The Method

Three steps, in order. Do not skip steps and do not start transcribing before completing the alphabet.

### Step 1: Build a Hand-Specific Alphabet

Before reading a single word, study the manuscript image and build a **letter-by-letter reference chart** for this particular scribe's hand. Every scribe forms letters differently — the general paleography guide tells you what secretary hand looks like in theory; this alphabet tells you what *this person's writing* looks like in practice.

For each letter of the alphabet (a–z), document:

- **Letterform**: How does this scribe form this letter? Describe the pen strokes — which direction, which are thick (downstrokes) and thin (upstrokes), where the lifts are.
- **Examples**: 2–4 words on the page where this letter appears clearly, with line references.
- **Confusion risks**: Which other letters could this be mistaken for in this specific hand?
- **Variants**: Does the scribe use more than one form (e.g., long-s vs. round-s, two styles of r)?

If a letter doesn't appear on the page, note that.

Also document:
- **Ligatures and combinations** — th, sh, ch, ff, the -es graph, the -er graph, etc.
- **Distinctive features** — decorative capitals, spacing habits, ink quality, anything that characterizes this hand.

#### Confusion Risk Ranking

At the end of the alphabet, rank the confusion risks from highest to lowest for this hand. For each one, explain:
- Which letters are being confused
- Why they look similar in this hand specifically
- What distinguishing feature (if any) can tell them apart

This ranking is your map of where errors are most likely. You'll consult it constantly during transcription.

**Save as:** `[manuscript]-alphabet.txt`

### Step 2: Transcribe the Page

Now transcribe, using your alphabet chart as your primary reference and the paleography guide as general background.

**How to read each word:**

1. Look at the pen strokes — what individual marks are on the page?
2. Match each stroke to a letterform in your alphabet chart
3. When you hit a high-risk confusion pair from your ranking, slow down and compare against the example words in the alphabet
4. Assemble the letters into a word
5. Only after you have a letterform-based reading, consider whether it makes sense in context

That last step is important: context can *confirm* a reading you've already made from letterforms, but it cannot *generate* a reading. "This looks like it says 'iuice' and that makes sense in a recipe" is good. "This is a recipe so the word is probably 'juice'" is not — that's fabrication.

#### The Cardinal Rule

**If you cannot read it, do not write it.**

Mark illegible text with `[...]`. A transcription full of gaps is more valuable than one full of guesses. Gaps are honest. Wrong guesses silently corrupt the historical record.

| What you see | What to do |
|---|---|
| Clear letterforms, unambiguous | Transcribe normally |
| Visible letterforms but ambiguous | Use `[word?]` flag |
| Some strokes visible, partial reading | Use `[b....es]` (letters you see + dots) |
| No letterforms distinguishable | Use `[...]` |
| Entire passage illegible | `[Passage illegible — ~N lines, reason]` |

#### Transcription Conventions

Follow Folger semi-diplomatic conventions (detailed in the paleography guide):

- **Preserve original spelling exactly** — "physicke" not "physic", "chirurgery" not "surgery"
- **Preserve original punctuation, capitalization, and line breaks**
- **Expand abbreviations** with supplied letters in *italics*
- **Preserve scribal errors** — dittography ("make make"), transposed letters ("littly"), false starts ("th the"). Transcribe what is there, not what was meant.
- **Preserve apostrophes** in possessives and contractions exactly as written
- **Do not modernize** anything — not u/v, not i/j, not long-s, not doubled consonants, not terminal -e

#### Common Errors to Watch For

These patterns have been observed across multiple blind transcription experiments. They are general early modern paleography problems, not specific to any one manuscript:

1. **Normalizing doubled consonants** — scribes wrote "putt," "itt," "hott." If you see two pen strokes, transcribe two letters.
2. **Dropping terminal -e** — "Coleworte," "handefull," "fundamente." If the letterform is there, keep it.
3. **Substituting familiar words** — recipe books contain plant names, medical terms, and archaic words that look strange. An unfamiliar transcription is more likely correct than a familiar-sounding guess.
4. **Confusing long-s (ſ) with f** — long-s has no crossbar or only a partial one on the left side. If there's a full crossbar through the stem, it's f.
5. **Modernizing u/v** — transcribe what the scribe wrote. "vpon" stays "vpon," "haue" stays "haue."
6. **Missing the -es graph** — a looped downstroke at the end of a word meaning -es. Easy to miss or read as a single letter.
7. **Misreading the -er graph** — a hook-shaped upstroke that can also mean -ar, -or, or -re depending on context.

### Step 3: Verify Against Vocabulary Reference

After completing the transcription, go back through it and check each unfamiliar or uncertain word against the vocabulary reference (`extracted/derived/vocab/vocab-reference.txt`).

**The rules for using the vocab list:**

1. **Read first, verify second.** Always complete your letterform-based reading before checking. The list confirms readings; it does not generate them.

2. **Word on the list** → your confidence increases. The word is attested in other early modern manuscripts.

3. **Word NOT on the list** → re-examine the letterforms. Is there a plausible alternative where one or two letters differ? If that alternative IS on the list and the letterforms genuinely support it, it may be correct. But if they don't, keep your original reading. The list doesn't contain every word.

4. **Never let the list override clear letterforms.** If you can clearly see the pen strokes and they spell a word not on the list, transcribe what you see. The list is evidence, not authority.

5. **Note verifications** in your confidence notes: "Read 'calcinated' — confirmed in vocab reference (attested in 6+ manuscripts)."

## Output Format

For each page, produce three files:

| File | Contents |
|------|----------|
| `[manuscript]-alphabet.txt` | Hand-specific letter chart with confusion risk ranking |
| `[manuscript]-transcription.txt` | **Plain transcription text only** — no headers, no metadata, no section markers |
| `[manuscript]-notes.txt` | Confidence notes listing flagged readings and why they are uncertain |

**The transcription file must contain ONLY the transcription itself** — the raw text preserving original spelling, punctuation, capitalization, and lineation. No `===` section markers, no manuscript name header, no date, no method description. Just the transcription starting from the first line of manuscript text. This is because the CER evaluation script (`compute_cer.py`) compares it character-by-character against the reference — any extra text inflates the error rate.

The notes file should contain:
- Manuscript name and page number
- Each flagged reading with the line number, what you read, why it's uncertain, and whether the vocab reference confirmed it

Use the manuscript name from the image filename (e.g., `henslow-ms688-page12-alphabet.txt`).

## What Not to Do

- **Do not transcribe without building the alphabet first.** That is the entire point of this method. Without it, you will read top-down and hallucinate.
- **Do not use the vocabulary list as a dictionary to guess words.** It verifies; it doesn't predict.
- **Do not "clean up" the transcription** by modernizing spelling, regularizing punctuation, or correcting what look like errors. Those may be the scribe's actual writing.
- **Do not fill in gaps from context.** If you can't see the letterforms, mark it `[...]` and move on.
