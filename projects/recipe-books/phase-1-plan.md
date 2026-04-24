# Phase 1 Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn 35+ FromThePage recipe book text files into per-book JSON files with recipe-level structure (title, body, number, position, page ref) plus extractable book-level metadata.

**Architecture:** Single Python script using stdlib only. Auto-detects one of three format styles per input file (paren-numbered, bare-number, unnumbered), applies the appropriate splitter, extracts book-level metadata from front matter heuristically. Writes one JSON per input text file. Also writes a parse-report summarizing each book (format detected, recipe count, warnings).

**Tech Stack:** Python 3 (stdlib: `json`, `re`, `pathlib`, `argparse`), pytest for tests.

**Commit strategy:** User requested the design doc (`project-plan.md`) and all Phase 1 work be committed together. Individual tasks below include a "stage" step rather than a "commit" step; a single consolidated commit happens in Task 11.

---

## File Structure

```
projects/recipe-books/
├── project-plan.md              # [exists] Design doc
├── phase-1-plan.md              # [this file]
├── .gitignore                   # [create] ignore __pycache__, .pytest_cache
├── ingest/
│   └── transcriptions/          # [create] symlinks to TMTR raw-text files
├── extracted/
│   ├── recipes/                 # [create] Phase 1 JSON output
│   └── schema/
│       └── phase-1-recipe.schema.json  # [create] schema definition
├── scripts/
│   ├── __init__.py              # [create] make scripts/ importable
│   └── parse_recipes.py         # [create] the parser
└── tests/
    ├── __init__.py              # [create] make tests/ importable
    ├── conftest.py              # [create] add scripts/ to sys.path
    ├── test_parse_recipes.py    # [create] tests
    └── fixtures/
        ├── sedley-sample.txt    # [create] paren-numbered fixture
        ├── bulkeley-sample.txt  # [create] bare-number fixture
        └── brumwich-sample.txt  # [create] unnumbered fixture
```

### Responsibilities

- **`scripts/parse_recipes.py`** — all parsing logic: format detection, three splitters, front-matter extractor, CLI wrapper, directory walker.
- **`extracted/schema/phase-1-recipe.schema.json`** — canonical schema for Phase 1 output, used for validation and documentation.
- **`tests/test_parse_recipes.py`** — unit tests for each splitter and the detector, integration test for the CLI.
- **`tests/fixtures/*.txt`** — small hand-crafted excerpts (~20–40 lines each) representing the three format styles. Real files from the TMTR raw-text folder are NOT checked in; tests use fixtures only.

---

## Task 1: Project scaffolding

**Files:**
- Create: `projects/recipe-books/.gitignore`
- Create: `projects/recipe-books/ingest/transcriptions/.gitkeep`
- Create: `projects/recipe-books/extracted/recipes/.gitkeep`
- Create: `projects/recipe-books/extracted/schema/.gitkeep`
- Create: `projects/recipe-books/scripts/__init__.py`
- Create: `projects/recipe-books/tests/__init__.py`
- Create: `projects/recipe-books/tests/fixtures/.gitkeep`

- [ ] **Step 1: Create `.gitignore`**

Path: `projects/recipe-books/.gitignore`

Content:
```
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
```

- [ ] **Step 2: Create the empty directory structure with .gitkeep sentinels**

Run these from repo root:
```bash
mkdir -p projects/recipe-books/ingest/transcriptions
mkdir -p projects/recipe-books/extracted/recipes
mkdir -p projects/recipe-books/extracted/schema
mkdir -p projects/recipe-books/scripts
mkdir -p projects/recipe-books/tests/fixtures
touch projects/recipe-books/ingest/transcriptions/.gitkeep
touch projects/recipe-books/extracted/recipes/.gitkeep
touch projects/recipe-books/extracted/schema/.gitkeep
touch projects/recipe-books/tests/fixtures/.gitkeep
```

- [ ] **Step 3: Create `scripts/__init__.py` and `tests/__init__.py` (empty files)**

```bash
touch projects/recipe-books/scripts/__init__.py
touch projects/recipe-books/tests/__init__.py
```

- [ ] **Step 4: Verify pytest is installed**

Run: `python3 -m pytest --version`

Expected: something like `pytest 7.x.x` or `pytest 8.x.x`.

If not installed, run: `pip3 install pytest` (or `python3 -m pip install pytest`).

- [ ] **Step 5: Create `tests/conftest.py` to make the script importable**

Path: `projects/recipe-books/tests/conftest.py`

Content:
```python
import sys
from pathlib import Path

# Add scripts/ to sys.path so tests can import parse_recipes
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
```

- [ ] **Step 6: Stage changes (do NOT commit yet — Task 11 does the consolidated commit)**

Run from repo root:
```bash
git add projects/recipe-books/
```

Verify with: `git status` — should show the new scaffolding files staged.

---

## Task 2: JSON schema definition

**Files:**
- Create: `projects/recipe-books/extracted/schema/phase-1-recipe.schema.json`

- [ ] **Step 1: Write the schema**

Path: `projects/recipe-books/extracted/schema/phase-1-recipe.schema.json`

Content:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Phase 1 Recipe Book",
  "description": "Minimal per-book schema produced by the deterministic parser. Per design doc § 3.",
  "type": "object",
  "required": ["ms_id", "book", "recipes"],
  "properties": {
    "ms_id": {
      "type": "string",
      "description": "Stable identifier, matches the input filename stem"
    },
    "book": {
      "type": "object",
      "required": ["title_raw", "recipe_count"],
      "properties": {
        "title_raw": { "type": ["string", "null"] },
        "date_inscribed": { "type": ["string", "null"] },
        "attributed_compiler": { "type": ["string", "null"] },
        "source_url": { "type": ["string", "null"] },
        "recipe_count": { "type": "integer" },
        "format_detected": {
          "type": "string",
          "enum": ["paren_numbered", "bare_number", "unnumbered", "unknown"]
        },
        "parse_warnings": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "recipes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["position", "raw_body"],
        "properties": {
          "recipe_number": { "type": ["integer", "null"] },
          "position": { "type": "integer" },
          "raw_title": { "type": ["string", "null"] },
          "raw_body": { "type": "string" },
          "page_ref": { "type": ["string", "null"] }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Sanity-check the schema is valid JSON**

Run: `python3 -c "import json; json.load(open('projects/recipe-books/extracted/schema/phase-1-recipe.schema.json'))"`

Expected: no output (success). If it errors, fix the JSON.

- [ ] **Step 3: Stage changes**

```bash
git add projects/recipe-books/extracted/schema/phase-1-recipe.schema.json
```

---

## Task 3: Create test fixtures

Small hand-crafted excerpts representing the three format styles. Each ~20–40 lines. These are NOT copies of real files — they're minimal examples that exercise the parsing rules.

**Files:**
- Create: `projects/recipe-books/tests/fixtures/sedley-sample.txt`
- Create: `projects/recipe-books/tests/fixtures/bulkeley-sample.txt`
- Create: `projects/recipe-books/tests/fixtures/brumwich-sample.txt`

- [ ] **Step 1: Write `sedley-sample.txt` (paren-numbered format)**

Path: `projects/recipe-books/tests/fixtures/sedley-sample.txt`

Content:
```
The Lady Sedley
her Receipt book
1686.

49

1.

A Receipt for the Dropsey.
(1)

Take Horehound, Harts tonge, Liverworth, Worm-
wood & Sorrill, of each a large handfull shred
them very small.
Probatum est.




2

To Make Snayle Water.
(2)

Take a good peck of garden Snayles in their shells
& wash them in a great bowle of beere.
```

- [ ] **Step 2: Write `bulkeley-sample.txt` (bare-number format)**

Path: `projects/recipe-books/tests/fixtures/bulkeley-sample.txt`

Content:
```
760

BULKELEY (Elizabeth)

A boke of hearbes and receipts

(Dated) 1627

MS.  No.169




2
The Vertues of sages

Sage is hot in the begininge of the third degree
it hath adioyninge noe litle astriction or byndinge.




3
The temperature of minte

Mint is hott & drye in the third degree, it is
some what bitter & harsh.
```

- [ ] **Step 3: Write `brumwich-sample.txt` (unnumbered format)**

Path: `projects/recipe-books/tests/fixtures/brumwich-sample.txt`

Content:
```
Brumwich (Anne) [& others]
Booke of Receipts or Medicines
[? out]
MS. No. 160.




An excillent Soveraighne balsome called the
Lady Ropa Ropeues

Take a quarter of a pound of yellow wax cutt into small peices
& putt itt into a new earthen pott or panne then melt itt.



A Medicine for a Cough

Take a pint of strong Ale and boyle it with Liquorish and
Aniseeds until halfe be consumed.
```

- [ ] **Step 4: Stage changes**

```bash
git add projects/recipe-books/tests/fixtures/
```

---

## Task 4: Paren-numbered splitter (Sedley style)

**Files:**
- Create: `projects/recipe-books/scripts/parse_recipes.py` (initial version with just this splitter)
- Create: `projects/recipe-books/tests/test_parse_recipes.py`

- [ ] **Step 1: Write the failing test**

Path: `projects/recipe-books/tests/test_parse_recipes.py`

Content:
```python
from pathlib import Path
from parse_recipes import split_paren_numbered

FIXTURES = Path(__file__).parent / "fixtures"


def test_paren_numbered_splits_sedley_sample():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    recipes = split_paren_numbered(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] == 1
    assert recipes[0]["raw_title"] == "A Receipt for the Dropsey."
    assert "Horehound" in recipes[0]["raw_body"]
    assert "Probatum est." in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] == 2
    assert recipes[1]["raw_title"] == "To Make Snayle Water."
    assert "garden Snayles" in recipes[1]["raw_body"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `projects/recipe-books/`:
```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'parse_recipes'`.

- [ ] **Step 3: Write the minimal implementation**

Path: `projects/recipe-books/scripts/parse_recipes.py`

Content:
```python
"""Phase 1 parser: FromThePage recipe book text → per-book JSON.

Handles three format styles (paren-numbered, bare-number, unnumbered),
auto-detects format per file, extracts book-level metadata from front matter.
"""

import re
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run from `projects/recipe-books/`:
```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: PASS. 1 test passed.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 5: Bare-number splitter (Bulkeley style)

**Files:**
- Modify: `projects/recipe-books/scripts/parse_recipes.py` (add new function)
- Modify: `projects/recipe-books/tests/test_parse_recipes.py` (add new test)

- [ ] **Step 1: Write the failing test**

Append to `projects/recipe-books/tests/test_parse_recipes.py`:

```python
from parse_recipes import split_bare_number


def test_bare_number_splits_bulkeley_sample():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    recipes = split_bare_number(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] == 2
    assert recipes[0]["raw_title"] == "The Vertues of sages"
    assert "Sage is hot" in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] == 3
    assert recipes[1]["raw_title"] == "The temperature of minte"
    assert "Mint is hott" in recipes[1]["raw_body"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py::test_bare_number_splits_bulkeley_sample -v
```

Expected: FAIL with `ImportError: cannot import name 'split_bare_number'`.

- [ ] **Step 3: Add the implementation**

Append to `projects/recipe-books/scripts/parse_recipes.py`:

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 6: Unnumbered splitter (Brumwich style)

The hardest case — no numeric markers. Recipe boundaries detected by title patterns: a short (<12-word) line preceded by ≥3 blank lines, where the line isn't all lowercase and doesn't end with punctuation other than a period.

This will produce lower-quality boundaries than the numbered formats. That's expected; we flag it.

**Files:**
- Modify: `projects/recipe-books/scripts/parse_recipes.py` (add new function)
- Modify: `projects/recipe-books/tests/test_parse_recipes.py` (add new test)

- [ ] **Step 1: Write the failing test**

Append to `projects/recipe-books/tests/test_parse_recipes.py`:

```python
from parse_recipes import split_unnumbered


def test_unnumbered_splits_brumwich_sample():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    recipes = split_unnumbered(text)

    assert len(recipes) == 2

    assert recipes[0]["recipe_number"] is None
    assert recipes[0]["position"] == 1
    assert "balsome" in recipes[0]["raw_title"]
    assert "yellow wax" in recipes[0]["raw_body"]

    assert recipes[1]["recipe_number"] is None
    assert recipes[1]["position"] == 2
    assert recipes[1]["raw_title"] == "A Medicine for a Cough"
    assert "strong Ale" in recipes[1]["raw_body"]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py::test_unnumbered_splits_brumwich_sample -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Add the implementation**

Append to `projects/recipe-books/scripts/parse_recipes.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 7: Format detector

Auto-detects which format a file is in by counting paren markers, bare-number markers, and fallback to unnumbered.

**Files:**
- Modify: `projects/recipe-books/scripts/parse_recipes.py`
- Modify: `projects/recipe-books/tests/test_parse_recipes.py`

- [ ] **Step 1: Write the failing test**

Append to `projects/recipe-books/tests/test_parse_recipes.py`:

```python
from parse_recipes import detect_format


def test_detect_format_paren_numbered():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    assert detect_format(text) == "paren_numbered"


def test_detect_format_bare_number():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    assert detect_format(text) == "bare_number"


def test_detect_format_unnumbered():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    assert detect_format(text) == "unnumbered"
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 3 new tests FAIL (ImportError).

- [ ] **Step 3: Add the implementation**

Append to `projects/recipe-books/scripts/parse_recipes.py`:

```python
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
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 8: Book-level metadata extractor

Extract book title, date, and attributed compiler from the front matter (content before the first recipe).

This is best-effort — front matter varies widely. Fields are nullable.

**Files:**
- Modify: `projects/recipe-books/scripts/parse_recipes.py`
- Modify: `projects/recipe-books/tests/test_parse_recipes.py`

- [ ] **Step 1: Write the failing test**

Append to `projects/recipe-books/tests/test_parse_recipes.py`:

```python
from parse_recipes import extract_book_metadata


def test_extract_book_metadata_sedley():
    text = (FIXTURES / "sedley-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["title_raw"] is not None
    assert "Sedley" in meta["title_raw"]
    assert meta["date_inscribed"] == "1686"


def test_extract_book_metadata_bulkeley():
    text = (FIXTURES / "bulkeley-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["attributed_compiler"] is not None
    assert "BULKELEY" in meta["attributed_compiler"].upper() or "Bulkeley" in meta["attributed_compiler"]
    assert meta["date_inscribed"] == "1627"


def test_extract_book_metadata_brumwich():
    text = (FIXTURES / "brumwich-sample.txt").read_text()
    meta = extract_book_metadata(text)
    assert meta["attributed_compiler"] is not None
    assert "Brumwich" in meta["attributed_compiler"]
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 3 new tests FAIL (ImportError).

- [ ] **Step 3: Add the implementation**

Append to `projects/recipe-books/scripts/parse_recipes.py`:

```python
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
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 9 tests PASS.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 9: CLI wrapper — directory walker + JSON writer

Main entry point: walks a directory, parses each `.txt` file, writes `{stem}.json` to an output directory, and emits a summary report.

**Files:**
- Modify: `projects/recipe-books/scripts/parse_recipes.py` (add main CLI)
- Modify: `projects/recipe-books/tests/test_parse_recipes.py` (integration test)

- [ ] **Step 1: Write the failing integration test**

Append to `projects/recipe-books/tests/test_parse_recipes.py`:

```python
import json
from parse_recipes import parse_file


def test_parse_file_produces_full_record(tmp_path):
    src = FIXTURES / "sedley-sample.txt"
    record = parse_file(src)

    assert record["ms_id"] == "sedley-sample"
    assert record["book"]["format_detected"] == "paren_numbered"
    assert record["book"]["recipe_count"] == 2
    assert record["book"]["date_inscribed"] == "1686"
    assert len(record["recipes"]) == 2
    assert record["recipes"][0]["raw_title"] == "A Receipt for the Dropsey."
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py::test_parse_file_produces_full_record -v
```

Expected: FAIL with ImportError.

- [ ] **Step 3: Add `parse_file` and CLI entrypoint**

Append to `projects/recipe-books/scripts/parse_recipes.py`:

```python
import argparse
import json
from pathlib import Path


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
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd projects/recipe-books && python3 -m pytest tests/test_parse_recipes.py -v
```

Expected: 10 tests PASS.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/scripts/parse_recipes.py projects/recipe-books/tests/test_parse_recipes.py
```

---

## Task 10: Run on the real corpus

Execute the parser against the actual TMTR raw-text folder and inspect results.

**Files:**
- Modify: `projects/recipe-books/ingest/transcriptions/` (add symlinks)
- Create: `projects/recipe-books/extracted/recipes/*.json` (outputs)
- Create: `projects/recipe-books/extracted/parse-report.json`

- [ ] **Step 1: Symlink the TMTR raw-text files into `ingest/transcriptions/`**

Run from repo root:
```bash
cd projects/recipe-books/ingest/transcriptions && \
  for f in ../../../teaching-machines-to-read/extracted/derived/vocab/raw-text/*.txt; do
    ln -sf "$f" "$(basename "$f")"
  done && \
  cd - && ls projects/recipe-books/ingest/transcriptions/ | head
```

Expected: list of .txt symlinks.

- [ ] **Step 2: Run the parser**

Run from repo root:
```bash
cd projects/recipe-books && python3 scripts/parse_recipes.py \
  ingest/transcriptions/ \
  extracted/recipes/ \
  --report extracted/parse-report.json
```

Expected: prints one line per file (ms_id, format, recipe count). No exceptions. ~35-40 JSON files written to `extracted/recipes/`.

- [ ] **Step 3: Inspect the parse report**

```bash
cat projects/recipe-books/extracted/parse-report.json | python3 -m json.tool | head -80
```

Note any books flagged as `unknown` format or with zero recipes. These are expected — the herbals (Gerard, Culpeper) are not recipe books and won't parse meaningfully. They should be moved out of `ingest/transcriptions/` before the enrichment phases.

- [ ] **Step 4: Spot-check one real book's output**

```bash
cat projects/recipe-books/extracted/recipes/sedley-ms534.json | python3 -m json.tool | head -40
```

Expected: recognizable structure matching the schema. `book.title_raw` has "Sedley" in it, `recipes[0].raw_title` starts with "A Receipt", etc.

If spot-checks reveal systematic parsing problems on real files that the fixtures didn't catch, iterate on the splitter for that format — add a regression test against a trimmed snippet of the real file, fix the function, re-run.

- [ ] **Step 5: Stage changes**

```bash
git add projects/recipe-books/ingest/transcriptions/ projects/recipe-books/extracted/
```

---

## Task 11: Consolidated commit

All changes — the design doc, the plan, and the Phase 1 implementation — in a single commit per user request.

- [ ] **Step 1: Verify what will be committed**

```bash
git status
```

Expected staged files (from Tasks 1–10):
- `projects/recipe-books/project-plan.md` (the design doc, moved here from docs/ earlier)
- `projects/recipe-books/phase-1-plan.md` (this plan)
- `projects/recipe-books/.gitignore`
- `projects/recipe-books/scripts/parse_recipes.py`
- `projects/recipe-books/scripts/__init__.py`
- `projects/recipe-books/tests/__init__.py`
- `projects/recipe-books/tests/conftest.py`
- `projects/recipe-books/tests/test_parse_recipes.py`
- `projects/recipe-books/tests/fixtures/sedley-sample.txt`
- `projects/recipe-books/tests/fixtures/bulkeley-sample.txt`
- `projects/recipe-books/tests/fixtures/brumwich-sample.txt`
- `projects/recipe-books/extracted/schema/phase-1-recipe.schema.json`
- `projects/recipe-books/extracted/recipes/*.json` (one per parsed file)
- `projects/recipe-books/extracted/parse-report.json`
- `projects/recipe-books/ingest/transcriptions/*.txt` (symlinks)
- `.gitkeep` sentinels in any remaining empty dirs

- [ ] **Step 2: Create the consolidated commit**

```bash
git commit -m "$(cat <<'EOF'
Add recipe-books project: design doc + Phase 1 parser

Creates projects/recipe-books/ with:
- project-plan.md — full project design, research questions, schema, 
  chapter structure, relationship to teaching-machines-to-read
- phase-1-plan.md — implementation plan for the deterministic parser
- scripts/parse_recipes.py — rule-based parser handling three format
  styles (paren-numbered, bare-number, unnumbered) with book-level
  metadata extraction and a parse-quality report
- tests/ — hand-crafted fixtures + unit tests for each splitter and
  the format detector
- extracted/recipes/ — parsed JSON output for the FromThePage corpus
  (consumed from teaching-machines-to-read via symlinks)
- extracted/parse-report.json — per-book parse summary

Phase 1 lays the foundation for Phase 2 close reading and Phase 3
rich LLM-driven extraction. See project-plan.md for the full research
framing around recipe books as a site of gendered knowledge 
production and genre obscuring.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify the commit**

```bash
git log -1 --stat
```

Expected: single commit with all the files listed above.

---

## Self-review notes

- **Spec coverage:** Tasks 1–11 implement §2 "Phase 1 — Parse (deterministic)" and §3 "Phase 1 schema" of the design doc. Phases 2–5 are out of scope for this plan.
- **No placeholders:** every step contains the exact command, path, or code needed.
- **Commit strategy:** deliberately deviates from per-task commits to honor user's "commit spec + Phase 1 together" instruction. All task-end steps use `git add` (stage) rather than `git commit` (commit).
- **Type consistency:** `parse_file()` builds a record matching the schema file. `detect_format()` returns one of the four enum values in the schema. `split_*()` functions all return `List[Dict]` with the same per-recipe shape.
- **Known gap accepted:** the unnumbered splitter will produce lower-quality boundaries on real books than the numbered splitters. The parse-report surfaces this via warnings; Phases 2–3 handle the messier cases via close reading and LLM extraction rather than more parsing rules.

---
