# Method: Diplomatic transcription of an English secretary-hand page

You are transcribing one page of an English secretary-hand recipe book (c. 1600–1700).
Work from the strokes up, not from your expectations down. Your goal is a faithful
diplomatic record of what is physically on the page — including its line structure —
not a clean modern reading. When you cannot read something, leave a gap; do not guess.

Follow these stages in order.

## Stage 1 — Study the hand before transcribing anything

Before writing a single line of transcription, look over the whole page and build a
private mental model of THIS scribe's hand:

- Find 3–4 words you are confident about. Use them to pin down how this scribe forms
  the common letters that cause the most trouble: secretary **e**, **c**, **r**, **t**,
  **d** (often looped/leftward), **h** (descends below the line), terminal **s** (often
  a round/sigma form or a long descender), and the two-stroke **w**.
- Note the scribe's **minims** (the short vertical strokes that make up i, u, n, m).
  Count strokes deliberately: `m` = three minims, `n`/`u` = two, and watch for `in`,
  `ni`, `iu`, `ui`, `un`, `nu` confusions — these are decided by stroke count, not guess.
- Note **long-s** (ſ): it looks like an f without the full crossbar. Transcribe it as a
  normal **s**. Distinguish it from real **f**. Note doubled long-s and ſs forms.
- Note this scribe's **abbreviations**: the macron/tilde over a vowel (= omitted m or n),
  the `wch`/`wth`/`yt`/`ye` forms, superscript letters, the `p`-with-stroke (per/par/pro),
  and the terminal flourish that may or may not mean a final letter.
- Note recurring **recipe vocabulary** the hand will repeat: take, ounce(s), pound,
  pint, quart, spoonful, handful, boil, distill, strain, water, oyle/oil, sugar, honey,
  vinegar, wine, herbs, and the symbols for ounce/dram. Recognizing the repeated word is
  more reliable than reading it letter-by-letter every time.

Do not output this model; it is your reference for Stage 2.

## Stage 2 — Read each line bottom-up: strokes → letters → words

Transcribe one physical line of the page at a time, top to bottom.

For any word you cannot read at a glance:
1. Read the **strokes** left to right (minims, ascenders, descenders, loops).
2. Group strokes into **letters** using the per-letter habits you learned in Stage 1.
3. Assemble letters into a **word**, and only then check it against likely recipe
   vocabulary. The image governs; vocabulary only confirms or breaks a tie between two
   readings the strokes already allow. Never let an expected word override strokes that
   clearly say something else.

## Stage 3 — Preserve the physical line structure and layout (do this exactly)

This is a diplomatic transcription, so the layout on the page is data. Reproduce it:

- **One manuscript line = one line of output.** Keep the scribe's line breaks exactly
  where they fall. Do NOT rewrap, merge, or re-flow lines to make sentences read smoothly.
- If a word is **split across two lines** (broken by the line end, with or without a
  hyphen), keep it split across two output lines exactly as written; reproduce the
  hyphen only if the scribe wrote one.
- Preserve **blank lines** between entries/recipes as blank lines in the output.
- Preserve the relative **indentation and centering** you can see: a centered or indented
  heading/title stays on its own line; an indented first line stays indented (use leading
  spaces). Do not invent indentation that isn't there.
- Keep **marginal notes, catchwords (the lone word at the bottom-right), page numbers,
  and headers** on their own lines, in roughly their page position (e.g. a right-margin
  note after the line it sits beside). Label a clearly marginal note as `[margin: ...]`.
- Preserve in-line spacing as single spaces; do not try to reproduce wide gaps as multiple
  spaces except for deliberate column/indent structure.

## Stage 4 — Spelling, capitals, and characters: keep them as written

- Transcribe the **original spelling** exactly. Do not modernize, correct, or expand
  silently (no "and" for "&", no fixing "boyle" to "boil").
- Keep **i/j** and **u/v** as the scribe wrote them (e.g. "vse", "iuyce").
- Keep the ampersand **&** as **&**.
- Expand an abbreviation only when you are certain, and wrap the supplied letters in
  square brackets, e.g. `w[hi]ch`, `Mr[is]`. If unsure, transcribe the abbreviation
  literally (e.g. `wch`, `ye`).
- Reproduce **deletions** the scribe struck through as `[struck: word]` and insertions
  (carets/interlineations) as `[ins: word]` placed where they belong in the line.

## Stage 5 — Gap rather than guess (the core rule)

You are scored on accuracy, and a wrong guessed word costs more than an honest gap.

- For a single illegible **letter**, write a middle dot `·` in its place.
- For an illegible **word**, write `[?]`.
- For a partly legible word, transcribe the letters you can read and mark the unreadable
  span, e.g. `boi··d`, `di[?]ll`.
- Use `[illegible]` for a longer unreadable stretch (several words or a damaged area).
- Never invent plausible filler text to bridge a gap, and never copy a guessed word just
  because it "fits" the recipe. An honest gap is correct; a confident wrong word is not.

## Output

Output only the transcription, line for line, matching the page's line structure and
layout per Stage 3. No commentary, no translation, no summary.
