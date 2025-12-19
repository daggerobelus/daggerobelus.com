#!/usr/bin/env python3
"""
Extract term counts from all 347 witchcraft trial PDFs.
Outputs a CSV with term frequencies for each trial, suitable for D3 visualization.

Usage:
    python extract_trial_terms.py

Requirements:
    pip install PyPDF2 pandas
"""

import os
import re
from pathlib import Path
from collections import Counter
import pandas as pd

# Try to import PDF library
try:
    from PyPDF2 import PdfReader
    PDF_LIBRARY = 'PyPDF2'
except ImportError:
    try:
        import pdfplumber
        PDF_LIBRARY = 'pdfplumber'
    except ImportError:
        print("ERROR: Please install a PDF library:")
        print("  pip install PyPDF2")
        print("  or")
        print("  pip install pdfplumber")
        exit(1)

# Configuration
ARCHIVE_DIR = Path("/Users/sarahbonanno/Desktop/Witchcraft/Archive_Complete")
OUTPUT_DIR = Path("/Users/sarahbonanno/Desktop/Witchcraft/figures/non_death_analysis")
OUTPUT_FILE = OUTPUT_DIR / "all_cases_term_counts.csv"

# Terms to count (case-insensitive)
TERMS = [
    'reputation', 'reputed', 'reputée', 'réputée',
    'suspected', 'suspect', 'soupçon',
    'accused', 'accusé', 'accusée',
    'witness', 'témoin', 'witnesses', 'témoins',
    'quarrel', 'querelle', 'dispute',
    'threat', 'menace', 'threatened', 'menaçé',
    'confess', 'confession', 'avoué', 'aveu', 'confessed',
    'sabbat', 'sabbath',
    'torture', 'tortured', 'rack', 'thumbscrew', 'question', 'tourment',
    'died', 'death', 'mort', 'décédé', 'exécuté', 'executed',
    'released', 'renvoyé', 'renvoyée', 'libéré',
    'banished', 'banni', 'bannie', 'exile',
]

# Group terms for aggregation
TERM_GROUPS = {
    'reputation': ['reputation', 'reputed', 'reputée', 'réputée'],
    'suspected': ['suspected', 'suspect', 'soupçon'],
    'accused': ['accused', 'accusé', 'accusée'],
    'witness': ['witness', 'témoin', 'witnesses', 'témoins'],
    'quarrel': ['quarrel', 'querelle', 'dispute'],
    'threat': ['threat', 'menace', 'threatened', 'menaçé'],
    'confess': ['confess', 'confession', 'avoué', 'aveu', 'confessed'],
    'sabbat': ['sabbat', 'sabbath'],
    'torture': ['torture', 'tortured', 'rack', 'thumbscrew', 'question', 'tourment'],
    'death': ['died', 'death', 'mort', 'décédé', 'exécuté', 'executed'],
    'released': ['released', 'renvoyé', 'renvoyée', 'libéré'],
    'banished': ['banished', 'banni', 'bannie', 'exile'],
}

# Known non-death outcomes (from non_death_cases_detailed.csv)
NON_DEATH_OUTCOMES = {
    'w014': 'released',
    'w016': 'unknown',
    'w017': 'unknown',
    'w020': 'unknown',
    'w021': 'unknown',
    'w033': 'unknown',
    'w034': 'released',
    'w064': 'banished',
    'w065': 'banished',
    'w082': 'unknown',
    'w086': 'unknown',
    'w089': 'unknown',
    'w090': 'banished',
    'w114': 'unknown',
    'w117': 'unknown',
    'w118': 'banished',
    'w132': 'banished',
    'w138': 'unknown',
    'w141': 'released',
    'w142': 'released',
    'w151': 'unknown',
    'w184': 'unknown',
    'w189': 'unknown',
    'w193': 'released',
    'w198': 'released',
    'w215': 'banished',
    'w216': 'unknown',
    'w235': 'banished',
    'w246': 'released',
    'w279': 'released',
    'w280': 'released',
    'w325': 'banished',
    'w330': 'unknown',
    'w341': 'unknown',
    'w344': 'banished',
}


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        if PDF_LIBRARY == 'PyPDF2':
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        else:  # pdfplumber
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"  Warning: Could not read {pdf_path.name}: {e}")
        return ""


def count_terms(text: str) -> dict:
    """Count occurrences of each term group in text."""
    text_lower = text.lower()
    counts = {}

    for group_name, terms in TERM_GROUPS.items():
        count = 0
        for term in terms:
            # Use word boundaries for accurate counting
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            count += len(re.findall(pattern, text_lower))
        counts[group_name] = count

    return counts


def extract_trial_id(filename: str) -> str:
    """Extract trial ID from filename (e.g., 'w001.pdf' -> 'w001')."""
    # Handle both 'w001.pdf' and 'Witch%20352.pdf' formats
    name = filename.replace('%20', ' ').replace('.pdf', '')

    # Try to extract w### format
    match = re.search(r'w(\d+)', name.lower())
    if match:
        return f"w{match.group(1).zfill(3)}"

    # Try "Witch ###" format
    match = re.search(r'witch\s*(\d+)', name.lower())
    if match:
        return f"w{match.group(1).zfill(3)}"

    return name


def get_outcome(trial_id: str) -> str:
    """Determine outcome for a trial."""
    if trial_id in NON_DEATH_OUTCOMES:
        return NON_DEATH_OUTCOMES[trial_id]
    return 'death_sentence'


def main():
    print("=" * 60)
    print("WITCHCRAFT TRIAL TERM EXTRACTION")
    print("=" * 60)
    print(f"\nUsing PDF library: {PDF_LIBRARY}")
    print(f"Archive directory: {ARCHIVE_DIR}")
    print(f"Output file: {OUTPUT_FILE}")

    # Find all PDF files
    pdf_files = list(ARCHIVE_DIR.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files")

    if len(pdf_files) == 0:
        print("ERROR: No PDF files found in Archive directory")
        return

    # Process each PDF
    results = []
    for i, pdf_path in enumerate(sorted(pdf_files)):
        trial_id = extract_trial_id(pdf_path.name)
        print(f"  [{i+1}/{len(pdf_files)}] Processing {pdf_path.name} -> {trial_id}")

        # Extract text
        text = extract_text_from_pdf(pdf_path)

        if not text:
            print(f"    Warning: No text extracted")
            continue

        # Count terms
        term_counts = count_terms(text)

        # Get outcome
        outcome = get_outcome(trial_id)

        # Build result row
        row = {
            'trial_id': trial_id,
            'filename': pdf_path.name,
            'outcome': outcome,
            'text_length': len(text),
            **term_counts
        }
        results.append(row)

    # Create DataFrame and save
    df = pd.DataFrame(results)

    # Sort by trial_id
    df = df.sort_values('trial_id').reset_index(drop=True)

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n{'=' * 60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nResults saved to: {OUTPUT_FILE}")
    print(f"Total trials processed: {len(df)}")

    # Print summary statistics
    print(f"\nOutcome distribution:")
    print(df['outcome'].value_counts().to_string())

    print(f"\nTerm count summary (means):")
    term_cols = list(TERM_GROUPS.keys())
    for term in term_cols:
        if term in df.columns:
            print(f"  {term}: {df[term].mean():.2f}")

    # Also create a summary by outcome
    summary = df.groupby('outcome')[term_cols].mean()
    summary_file = OUTPUT_DIR / "all_cases_term_summary.csv"
    summary.to_csv(summary_file)
    print(f"\nSummary by outcome saved to: {summary_file}")


if __name__ == "__main__":
    main()
