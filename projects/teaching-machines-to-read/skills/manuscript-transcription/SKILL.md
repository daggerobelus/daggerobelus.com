---
name: manuscript-transcription
description: >
  Transcribe early modern English manuscript pages written in secretary hand
  (roughly 1500–1700). Use this skill whenever you are asked to transcribe a
  manuscript image, read early modern handwriting, produce a semi-diplomatic
  transcription, or work with recipe books, letters, or other early modern
  documents — also when someone mentions paleography, secretary hand, or
  letterforms. When given multiple ordered pages of a single hand, it works
  through them in sets, building and reusing its own growing alphabet and
  revisiting earlier uncertain readings as its knowledge of the hand matures;
  for a single page it is the same method with one set.
---

# Manuscript Transcription — Learning a Hand by Reading It

You are transcribing an early modern English manuscript written in **a single scribe's hand** (secretary hand, roughly 1500–1700). The method is the same whether you have one page or a whole manuscript: read the hand bottom-up, build your own reference for how this scribe writes, and stay honest about what you cannot read.

When you have **multiple ordered pages of one hand**, you work through them **in sets, in order**, and you are expected to **get better at this hand as you go** — because the alphabet you build on early pages makes later pages readable. A single page (or a few pages) is just the degenerate case: one set, same method, and the revision step still helps you recover first-pass uncertainties.

This is a research transcription evaluated against field-standard CER and reviewed by paleography scholars. The *process* — how your reading of the hand develops — is itself of interest, so the materials you produce along the way matter as much as the final text.

## Your materials

- **Page image(s)** for one hand — when there are several, `images/pageNNN.jpg`, processed in numeric order.
- **Paleography guide** — `ingest/references/paleography-guide.md` (secretary letterforms, abbreviations, Folger semi-diplomatic conventions). Read it before starting.
- **Vocabulary reference** — `extracted/derived/vocab/vocab-reference.txt` (~19,000 words attested in early modern recipe books). A verification tool, not a prediction tool.
- **A working folder** — where every file you produce is saved (see *Output*).

If the exact locations differ from the above, use the paths you are given. If any material is missing, ask before proceeding.

## What makes this work (read before starting)

These are the commitments behind every step. They matter more than any rule, so understand the reasoning:

- **Read bottom-up, not top-down.** Match the pen strokes on the page to letterforms, assemble letters into words. Do not guess what word "should" be there from context — top-down reading is what produces hallucination and silent modernization. The alphabet you build is what keeps you bottom-up.
- **The alphabet is *yours*, and it grows.** You build your own reference for this scribe and extend it as you see more of the hand. A reader coming to know a hand is the heart of the method. Never transcribe from a reference someone else wrote; never copy habits from a different manuscript.
- **You will revise later, so flag freely now.** Across a hand, every set ends knowing more than it began. So when a word is unclear on first contact, *flagging it is the correct move, not a failure* — you are deferring the reading until you know the hand better, and there is a dedicated revision pass for exactly that. Do not force a reading you cannot see.
- **The vocab list confirms, it does not generate.** Read the letterforms first, *then* optionally check the word against the list. If you find yourself scanning the list for words that might fit a gap, stop — you have reversed the process.
- **Preserve everything.** Write every state to a file as you go — forward transcriptions, notes, every alphabet snapshot, every revision. Never overwrite a snapshot. The full record of how you worked is data, not scratch.

## The cycle

Process the pages **set by set, in order** (sets of ~5 pages; a short job may be a single set). For each set N:

### Step A — Forward pass (transcribe the set)

For each page in the set, working with your **current** alphabet (for set 1 you build it first — see Step B):

1. Look at the pen strokes. Match each to a letterform in your alphabet. Assemble letters into words.
2. If a word is unclear, you *may* check a candidate reading against the vocab reference — to confirm, never to generate.
3. Use the confidence scale below. When you cannot read something, leave the gap; you will return to it.

| What you can see | What to write |
|---|---|
| Clear strokes, unambiguous reading | The word |
| Strokes visible but ambiguous (two possible readings) | `[word?]` |
| Some strokes visible, rest unclear | `[b....es]` (letters you can trace + dots) |
| No traceable strokes | `[...]` |
| Whole passage illegible | `[Passage illegible — ~N lines, reason]` |

Save each page's transcription as `set-NN/pageNNN-forward.txt` (plain transcription text only — no headers or metadata). Record every flagged reading in `set-NN/pageNNN-notes.txt` (line, your reading, why uncertain, any vocab check).

### Step B — Consolidate (update and snapshot your alphabet)

Update what you know about the hand from this set.

**For set 1**, build the alphabet from scratch first, *before* transcribing — scan the whole first set, find the clearest words, and for each letter a–z document:
- how this scribe forms it (stroke direction, thick/thin, lifts),
- 2–4 clear example words,
- confusion risks (which letters look alike in this hand),
- variants (e.g. long-s vs round-s), plus ligatures (th, ff, the -es and -er graphs).
Also note orthographic habits: u or v word-initially? doubled final consonants (itt/it)? terminal -e? i or j? **Calibrate:** transcribe 5 clear words letter-by-letter with your alphabet and check them against the vocab reference; if 3+ match no attested word, your alphabet has errors — fix it before transcribing the set.

**For every later set**, revise and extend the alphabet with what this set taught you: new letterforms, resolved confusions, corrected habits, newly-seen abbreviations.

Then **write a new numbered snapshot**: `alphabet-after-set-NN.txt`. **Never overwrite a previous snapshot** — the sequence `alphabet-after-set-01.txt`, `-02.txt`, … is the record of how your reading of the hand developed, and it must remain readable (diffable) afterward.

### Step C — Rolling revision (revisit earlier uncertainties)

With your freshly updated alphabet, go back to **every still-open flag** (`[word?]`, `[...]`, partial `[b..es]`) from **all sets so far**, earliest first. For each:

1. Look at the gap again on the page. Can you now trace strokes you missed?
2. Match them against your *current* alphabet — do letters resolve that didn't before?
3. If you can propose a reading, optionally confirm it against the vocab reference. If you still cannot read it, **leave the gap** — an honest `[...]` is the correct transcription, not a failure.

This is **not** a free re-edit of the whole text. Touch only the spans you previously flagged. You are testing whether knowing the hand better lets you read what you couldn't before — not second-guessing readings you were confident about.

For each span you revisit, append an entry to `revisions/revision-log.md`:

```
## set NN revision round — pageNNN, line L
flag: [original marker]
before: <what you had>
after:  <new reading, or still [...]>
why:    <what in the hand let you read it now — or why it stays a gap>
```

When a page's text changes, save the new version as `revisions/pageNNN-after-setNN.txt` (versioned — do not overwrite the forward file or earlier revisions). The "current" reading of any page is its latest version.

→ Then move to the next set and repeat A → B → C.

**After the final set**, do one optional final revision pass over any still-open flags with the fully matured alphabet, then assemble the latest version of every page into `final/pageNNN.txt`.

## Transcription conventions

Follow Folger semi-diplomatic conventions (detailed in the paleography guide):

- Preserve original spelling exactly — "physicke" not "physic".
- Preserve original punctuation, capitalization, and line breaks.
- Expand abbreviations with supplied letters in *italics*.
- Preserve scribal errors — dittography, transpositions, false starts.
- Keep the scribe's orthography — u/v, i/j, long-s, doubled consonants, terminal -e. If the scribe wrote "vpon," transcribe "vpon." The scribe's spelling is the data.

## Output (preserve everything)

Produce these in your working folder. Transcription files contain **only** transcription text — no manuscript name, date, or method notes — because CER compares character-by-character and any extra text inflates the error rate.

| Path | Contents |
|---|---|
| `set-NN/pageNNN-forward.txt` | Forward-pass transcription of each page (immutable once written) |
| `set-NN/pageNNN-notes.txt` | Flagged readings for that page |
| `alphabet-after-set-NN.txt` | Numbered alphabet snapshot — one per set, **never overwritten** |
| `revisions/revision-log.md` | Every revisit: set, page, line, before → after, why |
| `revisions/pageNNN-after-setNN.txt` | Revised page version (only when a page changed; versioned) |
| `final/pageNNN.txt` | Latest/best version of each page, assembled at the end |

Do not evaluate your own work against any reference — you never see one. A separate evaluator computes CER. Your job is an honest, bottom-up reading of the hand that gets better as you learn it.
