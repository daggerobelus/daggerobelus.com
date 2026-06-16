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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: clean_reference.py INPUT.txt [OUTPUT.txt]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], errors="replace") as f:
        out = clean(f.read())
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w") as f:
            f.write(out)
    else:
        sys.stdout.write(out)
