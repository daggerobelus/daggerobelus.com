"""Phase 1 parser: FromThePage recipe book text → per-book JSON.

Handles three format styles (paren-numbered, bare-number, unnumbered),
auto-detects format per file, extracts book-level metadata from front matter.
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional


# Matches lines that are just "(N)" or "(N.)" — recipe markers in Sedley style.
_PAREN_NUMBER_RE = re.compile(r"^\s*\((\d+)\.?\)\s*$", re.MULTILINE)


def split_paren_numbered(text: str) -> List[Dict]:
    """Split text into recipes using paren-numbered markers like "(1)", "(2)".

    The title is taken from the non-empty line immediately preceding
    the paren marker. The body runs from the line after the marker up
    to (but not including) the next marker's title — or end of file.
    """
    lines = text.split("\n")
    # Find every marker line, keeping the match so we don't regex twice.
    markers = []
    for i, line in enumerate(lines):
        m = _PAREN_NUMBER_RE.match(line)
        if m:
            markers.append((i, m))
    marker_indices = [i for i, _ in markers]

    recipes = []
    for idx, (marker_i, marker_match) in enumerate(markers):
        number = int(marker_match.group(1))

        # Title: nearest non-empty line above the marker.
        title = None
        for j in range(marker_i - 1, -1, -1):
            if lines[j].strip():
                title = lines[j].strip()
                break

        # Body: from line after marker up to the line before the next
        # marker's title, or end of file for the last recipe.
        body_start = marker_i + 1
        if idx + 1 < len(marker_indices):
            next_marker_i = marker_indices[idx + 1]
            # Find the next title (the non-empty line above next marker).
            body_end = next_marker_i
            for j in range(next_marker_i - 1, marker_i, -1):
                if lines[j].strip():
                    body_end = j
                    break
        else:
            body_end = len(lines)

        body = "\n".join(lines[body_start:body_end]).strip()

        recipes.append({
            "recipe_number": number,
            "position": idx + 1,
            "raw_title": title,
            "raw_body": body,
            "page_ref": None,
        })

    return recipes


# Matches lines that are just a digit (1-4 digits), possibly with trailing period.
# The tricky part: this would match page numbers too. We apply it AFTER a
# sufficient blank gap to distinguish from in-text numbers.
_BARE_NUMBER_RE = re.compile(r"^\s*(\d{1,4})\.?\s*$")

# A "gap" between recipes is >=3 blank lines — bulkeley-style books
# separate recipes with lots of whitespace.
_GAP_THRESHOLD = 3


def split_bare_number(text: str) -> List[Dict]:
    """Split text into recipes using bare-number markers on their own line,
    preceded by a sufficient gap of blank lines.

    Title follows the marker on the next non-empty line.
    """
    lines = text.split("\n")

    # Find candidate marker lines: a bare number preceded by >=3 blanks.
    # Keep the match object so we don't regex twice.
    markers = []
    for i, line in enumerate(lines):
        m = _BARE_NUMBER_RE.match(line)
        if not m:
            continue
        # Count blank lines immediately before this one.
        blanks = 0
        for j in range(i - 1, -1, -1):
            if lines[j].strip() == "":
                blanks += 1
            else:
                break
        if blanks >= _GAP_THRESHOLD:
            markers.append((i, m))
    marker_indices = [i for i, _ in markers]

    recipes = []
    for idx, (marker_i, marker_match) in enumerate(markers):
        number = int(marker_match.group(1))

        # Title: next non-empty line after the marker.
        title = None
        title_i = marker_i
        for j in range(marker_i + 1, len(lines)):
            if lines[j].strip():
                title = lines[j].strip()
                title_i = j
                break

        # Body: lines from after the title to the next marker (or EOF).
        body_start = title_i + 1
        if idx + 1 < len(marker_indices):
            body_end = marker_indices[idx + 1]
        else:
            body_end = len(lines)

        body = "\n".join(lines[body_start:body_end]).strip()

        recipes.append({
            "recipe_number": number,
            "position": idx + 1,
            "raw_title": title,
            "raw_body": body,
            "page_ref": None,
        })

    return recipes


def _looks_like_title(line: str) -> bool:
    """Heuristic: a line that could be a recipe title."""
    s = line.strip()
    if not s:
        return False
    if len(s.split()) > 12:
        return False  # too long to be a title
    if s == s.lower():
        return False  # all lowercase — probably body text
    if s.endswith((",", ";", ":", "&", "-")):
        return False  # continuation of previous line
    return True


def split_unnumbered(text: str) -> List[Dict]:
    """Split text into recipes using title-pattern heuristics (no numeric markers).

    A boundary: a line satisfying _looks_like_title(), preceded by
    at least _GAP_THRESHOLD blank lines. Titles may span multiple
    consecutive short lines (common in longer descriptive titles).
    """
    lines = text.split("\n")

    # Find title starts.
    title_start_indices = []
    for i, line in enumerate(lines):
        if not _looks_like_title(line):
            continue
        # Require the gap of blanks above.
        blanks = 0
        for j in range(i - 1, -1, -1):
            if lines[j].strip() == "":
                blanks += 1
            else:
                break
        if blanks >= _GAP_THRESHOLD:
            title_start_indices.append(i)

    recipes = []
    for idx, title_i in enumerate(title_start_indices):
        # Title may span multiple consecutive non-blank lines.
        title_end = title_i
        for j in range(title_i + 1, len(lines)):
            if lines[j].strip() == "":
                break
            title_end = j
        title = " ".join(lines[title_i:title_end + 1]).strip()
        title = re.sub(r"\s+", " ", title)

        body_start = title_end + 1
        if idx + 1 < len(title_start_indices):
            body_end = title_start_indices[idx + 1]
        else:
            body_end = len(lines)

        body = "\n".join(lines[body_start:body_end]).strip()

        recipes.append({
            "recipe_number": None,
            "position": idx + 1,
            "raw_title": title,
            "raw_body": body,
            "page_ref": None,
        })

    return recipes


# Minimum markers required to call a format "confidently detected".
_MIN_MARKERS_FOR_FORMAT = 2


def detect_format(text: str) -> str:
    """Returns one of: paren_numbered, bare_number, unnumbered, unknown.

    Strategy: count paren markers and gap-preceded bare-number markers.
    Whichever is higher (above threshold) wins. If both are below
    threshold, fall back to unnumbered.
    """
    lines = text.split("\n")

    paren_count = sum(
        1 for line in lines if _PAREN_NUMBER_RE.match(line)
    )

    bare_count = 0
    for i, line in enumerate(lines):
        if not _BARE_NUMBER_RE.match(line):
            continue
        blanks = 0
        for j in range(i - 1, -1, -1):
            if lines[j].strip() == "":
                blanks += 1
            else:
                break
        if blanks >= _GAP_THRESHOLD:
            bare_count += 1

    if paren_count >= _MIN_MARKERS_FOR_FORMAT and paren_count >= bare_count:
        return "paren_numbered"
    if bare_count >= _MIN_MARKERS_FOR_FORMAT:
        return "bare_number"
    # Fall back to unnumbered only if we can find SOMETHING title-like.
    for i, line in enumerate(lines):
        if not _looks_like_title(line):
            continue
        blanks = 0
        for j in range(i - 1, -1, -1):
            if lines[j].strip() == "":
                blanks += 1
            else:
                break
        if blanks >= _GAP_THRESHOLD:
            return "unnumbered"
    return "unknown"


# Four-digit year, rough range covering early modern recipe books.
_DATE_RE = re.compile(r"\b(1[4-8]\d{2})\b")

# Matches "NAME (Given)" or "NAME" in all-caps, with optional paren given name.
_COMPILER_CAPS_RE = re.compile(r"^\s*([A-Z][A-Z ]{2,})\s*(?:\(([^)]+)\))?\s*$")

# Matches "Name (given) [extras]" with mixed case — Brumwich-style.
_COMPILER_MIXED_RE = re.compile(
    r"^\s*([A-Z][a-z]+(?:[A-Z][a-z]+)?)\s*\(([^)]+)\)(?:\s*\[[^\]]*\])?\s*$"
)

# Keywords typical of recipe book title pages. Used to anchor the
# block-extension title extraction.
_TITLE_KEYWORD_RE = re.compile(
    r"\b(receipt|boke|book|medicines|hearbes)\b", re.IGNORECASE
)


def extract_book_metadata(text: str) -> Dict[str, Optional[str]]:
    """Best-effort extraction of book-level metadata from front matter.

    The "front matter" is taken to be everything before the first detected
    recipe boundary. For unnumbered format the whole text is scanned up
    to the first detected title.

    All fields may be None.
    """
    fmt = detect_format(text)

    # Determine the front-matter cutoff index.
    lines = text.split("\n")
    cutoff = len(lines)
    if fmt == "paren_numbered":
        for i, line in enumerate(lines):
            if _PAREN_NUMBER_RE.match(line):
                cutoff = i
                break
    elif fmt == "bare_number":
        for i, line in enumerate(lines):
            if not _BARE_NUMBER_RE.match(line):
                continue
            blanks = 0
            for j in range(i - 1, -1, -1):
                if lines[j].strip() == "":
                    blanks += 1
                else:
                    break
            if blanks >= _GAP_THRESHOLD:
                cutoff = i
                break
    elif fmt == "unnumbered":
        for i, line in enumerate(lines):
            if not _looks_like_title(line):
                continue
            blanks = 0
            for j in range(i - 1, -1, -1):
                if lines[j].strip() == "":
                    blanks += 1
                else:
                    break
            if blanks >= _GAP_THRESHOLD:
                cutoff = i
                break

    front_matter_lines = lines[:cutoff]
    front_matter = "\n".join(front_matter_lines)

    # Date: first plausible year in front matter.
    date_match = _DATE_RE.search(front_matter)
    date_inscribed = date_match.group(1) if date_match else None

    # Compiler + title from front-matter line scanning.
    compiler = None
    title_raw = None
    for i, line in enumerate(front_matter_lines):
        if compiler is None:
            m = _COMPILER_CAPS_RE.match(line)
            if m:
                compiler = m.group(0).strip()
                continue
            m = _COMPILER_MIXED_RE.match(line)
            if m:
                compiler = m.group(0).strip()
                continue
        # Title candidate: the first non-trivial line that mentions
        # "receipt", "boke", "book", "medicines", etc. — typical of
        # recipe book title pages. Extend backwards to include preceding
        # non-blank lines in the same block (e.g. "The Lady Sedley /
        # her Receipt book").
        if title_raw is None and _TITLE_KEYWORD_RE.search(line):
            # Collect the contiguous block of non-blank lines containing
            # this line, starting from the block's first line.
            block_start = i
            for j in range(i - 1, -1, -1):
                if front_matter_lines[j].strip():
                    block_start = j
                else:
                    break
            block_end = i
            for j in range(i + 1, len(front_matter_lines)):
                if front_matter_lines[j].strip():
                    block_end = j
                else:
                    break
            title_raw = " ".join(
                l.strip()
                for l in front_matter_lines[block_start : block_end + 1]
                if l.strip()
            )

    return {
        "title_raw": title_raw,
        "date_inscribed": date_inscribed,
        "attributed_compiler": compiler,
        "source_url": None,
    }


# Dispatch table from detected format to splitter.
_SPLITTERS = {
    "paren_numbered": split_paren_numbered,
    "bare_number": split_bare_number,
    "unnumbered": split_unnumbered,
}


def parse_file(path: Path) -> Dict:
    """Parse a single text file into a per-book record."""
    path = Path(path)
    text = path.read_text()
    fmt = detect_format(text)
    warnings: List[str] = []

    if fmt == "unknown":
        warnings.append("No recipe boundaries detected — output has zero recipes.")
        recipes: List[Dict] = []
    else:
        recipes = _SPLITTERS[fmt](text)
        if len(recipes) == 0:
            warnings.append(f"Format detected as {fmt} but zero recipes extracted.")

    meta = extract_book_metadata(text)

    if meta["title_raw"] is None:
        warnings.append("Book title not extracted from front matter.")
    if meta["date_inscribed"] is None:
        warnings.append("Book date not extracted from front matter.")
    if meta["attributed_compiler"] is None:
        warnings.append("Attributed compiler not extracted from front matter.")

    return {
        "ms_id": path.stem,
        "book": {
            "title_raw": meta["title_raw"],
            "date_inscribed": meta["date_inscribed"],
            "attributed_compiler": meta["attributed_compiler"],
            "source_url": meta["source_url"],
            "recipe_count": len(recipes),
            "format_detected": fmt,
            "parse_warnings": warnings,
        },
        "recipes": recipes,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_dir", type=Path, help="Directory of input .txt files")
    p.add_argument("output_dir", type=Path, help="Directory for JSON output")
    p.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path for a summary parse-report JSON",
    )
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    report = []
    for txt_path in sorted(args.input_dir.glob("*.txt")):
        record = parse_file(txt_path)
        out_path = args.output_dir / f"{record['ms_id']}.json"
        out_path.write_text(json.dumps(record, indent=2) + "\n")
        report.append({
            "ms_id": record["ms_id"],
            "format_detected": record["book"]["format_detected"],
            "recipe_count": record["book"]["recipe_count"],
            "date_inscribed": record["book"]["date_inscribed"],
            "attributed_compiler": record["book"]["attributed_compiler"],
            "warnings": record["book"]["parse_warnings"],
        })
        print(
            f"{record['ms_id']}: {record['book']['format_detected']} "
            f"({record['book']['recipe_count']} recipes)"
        )

    if args.report is not None:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
