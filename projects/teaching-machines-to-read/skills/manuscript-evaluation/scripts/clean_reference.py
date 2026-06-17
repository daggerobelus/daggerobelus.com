#!/usr/bin/env python3
"""
clean_reference.py — strip transcription-extraneous structural artifacts.

FromThePage reference transcriptions carry markup that a paleographic
transcription deliberately omits: the manuscript's own recipe/page numbers
on their own line, FromThePage recipe-segment counters like "(1)", brace
annotations like "{page break}", and end-of-line hyphenation that splits a
single word across two lines. Left in, every one of these counts as a CER
"error" against an agent that (correctly) doesn't reproduce them, inflating
CER uniformly.

Apply this to BOTH the reference and the hypothesis before CER, so the
comparison is symmetric — whatever each side does with these artifacts, they
are normalized the same way. Spelling, punctuation, capitalization, and real
line breaks are untouched.

Usage:
    python3 clean_reference.py INPUT.txt OUTPUT.txt
    python3 clean_reference.py INPUT.txt          # prints to stdout
"""
import re
import sys


def clean(text):
    # 1. Join end-of-line hyphenation, across the reference's blank lines:
    #    "Worm-\n\nwood" -> "Wormwood" (word-continuation hyphen isn't text).
    text = re.sub(r'-[ \t]*\n+[ \t]*', '', text)

    # 2. Remove FromThePage recipe-segment counters: "(1)", "(2)", ...
    text = re.sub(r'\(\d+\)', '', text)

    # 3. Remove brace annotations: "{page break}", "{catchword}", etc.
    text = re.sub(r'\{[^}]*\}', '', text)

    # 4. Drop lines that are ONLY a manuscript page/recipe number ("1.", "16")
    #    or a standalone roman numeral ("iv.", "XLI"). Inline numbers (quantities)
    #    are untouched because only whole-line matches are dropped.
    kept = []
    for line in text.split('\n'):
        s = line.strip()
        if re.fullmatch(r'\d+\.?', s):
            continue
        if re.fullmatch(r'[ivxlcdmIVXLCDM]+\.?', s):
            continue
        kept.append(line)
    text = '\n'.join(kept)

    # 5. Flatten ALL whitespace (newlines + runs of spaces) to single spaces.
    #    This is a deliberate choice: measure READING accuracy (did it get the
    #    words right), not lineation/spacing fidelity. Applied to BOTH sides, so
    #    the reference's double-spacing and any line-break differences drop out.
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def reading_normalize(text):
    """
    Modernization-tolerant ("reading") normalization, applied AFTER clean().

    Collapses early-modern orthographic *variants* to a canonical form on BOTH
    sides, so spelling-modernization that preserves the word ("vse"/"use") stops
    counting as an error. This measures READING accuracy (did the agent identify
    the right word) as distinct from DIPLOMATIC fidelity (did it preserve the
    scribe's exact orthography). Report BOTH; the gap between them is the cost of
    modernization, and is itself a finding.

    Conservative set — only transformations that do not change word identity:
      - lowercase (capitalization is not a reading error)
      - long-s -> s
      - u/v interchange and i/j interchange (positional graphic variants;
        canonicalized to u and i). Catches vses/uses, vppon/uppon, vntill/untill.
      - terminal -inge -> -ing (morninge -> morning)
      - drop apostrophes (approv'd / approved; the scribe's variable possessive)

    Deliberately NOT included (risk collapsing distinct words): general doubled-
    consonant reduction, terminal -e stripping, -ie/-y. Add these only with care.
    """
    text = text.lower()
    text = text.replace('ſ', 's')               # long-s ſ
    text = text.replace('v', 'u').replace('j', 'i')   # u/v, i/j
    text = re.sub(r'inge\b', 'ing', text)             # -inge -> -ing
    text = text.replace("'", '').replace('’', '')  # apostrophes
    text = re.sub(r'\s+', ' ', text).strip()
    return text


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--reading"]
    reading = "--reading" in sys.argv
    if not args:
        print("usage: clean_reference.py [--reading] INPUT.txt [OUTPUT.txt]", file=sys.stderr)
        print("  default: structural cleaning (DIPLOMATIC CER)", file=sys.stderr)
        print("  --reading: also collapse modernization variants (READING CER)", file=sys.stderr)
        sys.exit(1)
    with open(args[0], errors="replace") as f:
        out = clean(f.read())
    if reading:
        out = reading_normalize(out)
    if len(args) >= 2:
        with open(args[1], "w") as f:
            f.write(out)
    else:
        sys.stdout.write(out)
