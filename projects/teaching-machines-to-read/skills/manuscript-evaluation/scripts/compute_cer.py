#!/usr/bin/env python3
"""
compute_cer.py — Deterministic Character Error Rate (CER) Calculator
====================================================================

A reproducible measurement instrument for evaluating manuscript transcription
accuracy. Uses jiwer (the standard CER/WER library used in HTR/OCR benchmarks
including Transkribus evaluation) for edit distance computation.

The normalization pipeline strips AI confidence markers and illegibility
annotations while preserving all orthographic features of the original
manuscript (spelling, punctuation, capitalization, early modern letterforms
like long-s, u/v, i/j).

Dependencies:
    pip install -r requirements.txt
    (jiwer >= 3.0, numpy >= 1.24, scipy >= 1.10)

Usage:
    python compute_cer.py reference.txt hypothesis.txt
    python compute_cer.py reference.txt hypothesis.txt --raw
    python compute_cer.py reference.txt hypothesis.txt --verbose

Output:
    JSON to stdout (or just the CER number with --raw).

Part of the Teaching Machines to Read project — daggerobelus.com
"""

import argparse
import json
import re
import sys

import jiwer


# ---------------------------------------------------------------------------
# NORMALIZATION PIPELINE
# ---------------------------------------------------------------------------
# Each step is a separate function so reviewers can inspect exactly what
# happens, in what order, and verify that nothing substantive is altered.
#
# Order matters! We strip confidence markers first (they may contain
# brackets), then illegibility markers, then normalize whitespace last.
#
# IMPORTANT: We do NOT use jiwer's built-in transforms for normalization.
# jiwer's default transforms are designed for modern speech recognition
# (lowercasing, removing punctuation, etc.) which would destroy the
# orthographic features we need to preserve in early modern manuscripts.
# Our normalization is manuscript-specific and must be explicit.
# ---------------------------------------------------------------------------


def strip_frontmatter(text):
    """
    Step 0: Remove YAML-style frontmatter / metadata headers.

    Many transcription files begin with metadata (source, manuscript name,
    page number, transcription type, IIIF URLs, etc.) separated from the
    actual transcription by a '---' line. This metadata is not part of
    the manuscript text and should not contribute to CER.

    We strip everything up to and including the FIRST '---' line that
    appears within the first 20 lines. If no '---' is found, the text
    is returned unchanged.

    Returns:
        tuple: (cleaned_text, list of log entries, lines_stripped)
    """
    log = []
    lines = text.split('\n')

    # Only look in the first 20 lines for a --- separator
    for i, line in enumerate(lines[:20]):
        if line.strip() == '---':
            stripped_lines = i + 1
            log.append(f"Stripped {stripped_lines} header line(s) before '---' separator")
            return '\n'.join(lines[i + 1:]), log, stripped_lines

    return text, log, 0


def strip_confidence_markers(text):
    """
    Step 1: Remove AI confidence markers.

    These are annotations that AI transcription agents add to signal
    uncertainty. They are NOT part of the manuscript text.

    Patterns removed:
      - [?]           — standalone uncertainty flag
      - [word?]       — uncertain reading, replaced with just the word
      - {context: …}  — contextual notes added by the agent

    Returns:
        tuple: (cleaned_text, list of log entries, uncertain_count)
    """
    log = []
    uncertain_count = 0

    # --- Pattern: {context: ...} notes ---
    context_notes = re.findall(r'\{context:\s*[^}]*\}', text)
    if context_notes:
        log.append(f"Stripped {len(context_notes)} context note(s): {context_notes}")
        text = re.sub(r'\{context:\s*[^}]*\}', '', text)

    # --- Pattern: [word?] — uncertain reading ---
    # The brackets and question mark are removed; the word itself is kept.
    # This must come BEFORE stripping standalone [?] so we don't partially
    # match and leave orphaned text.
    uncertain_matches = re.findall(r'\[([^\[\]]+?)\?\]', text)
    if uncertain_matches:
        uncertain_count = len(uncertain_matches)
        log.append(f"Stripped uncertainty markers from {uncertain_count} word(s): {uncertain_matches}")
        text = re.sub(r'\[([^\[\]]+?)\?\]', r'\1', text)

    # --- Pattern: [?] — standalone uncertainty flag ---
    standalone_uncertain = len(re.findall(r'\[\?\]', text))
    if standalone_uncertain:
        uncertain_count += standalone_uncertain
        log.append(f"Stripped {standalone_uncertain} standalone [?] marker(s)")
        text = re.sub(r'\[\?\]', '', text)

    return text, log, uncertain_count


def strip_illegibility_markers(text):
    """
    Step 2: Remove illegibility markers and track how much was skipped.

    These markers indicate passages the transcriber could not read.
    We remove them from the text but count the characters they represent
    so we can compute a "coverage" metric — how much of the manuscript
    was actually attempted.

    Patterns removed:
      - [...]                        — generic gap marker
      - [passage illegible ...]      — descriptive illegibility note
      - [illegible]                  — simple illegibility flag
      - [N chars illegible]          — counted illegibility
      - [b....es]                    — partial reading with dots for unknown chars

    Returns:
        tuple: (cleaned_text, list of log entries, gap_count, illegible_char_estimate)
    """
    log = []
    gap_count = 0
    illegible_chars = 0

    # --- Pattern: [N chars illegible] or [N characters illegible] ---
    counted_gaps = re.findall(r'\[(\d+)\s+char(?:acter)?s?\s+illegible\]', text, re.IGNORECASE)
    if counted_gaps:
        for n in counted_gaps:
            illegible_chars += int(n)
            gap_count += 1
        log.append(f"Found {len(counted_gaps)} counted illegibility marker(s) totaling {illegible_chars} chars")
        text = re.sub(r'\[\d+\s+char(?:acter)?s?\s+illegible\]', '', text, flags=re.IGNORECASE)

    # --- Pattern: [passage illegible ...] or [line illegible] etc. ---
    descriptive_gaps = re.findall(r'\[(?:passage|line|word|text)\s+illegible[^\]]*\]', text, re.IGNORECASE)
    if descriptive_gaps:
        gap_count += len(descriptive_gaps)
        log.append(f"Found {len(descriptive_gaps)} descriptive illegibility marker(s): {descriptive_gaps}")
        text = re.sub(r'\[(?:passage|line|word|text)\s+illegible[^\]]*\]', '', text, flags=re.IGNORECASE)

    # --- Pattern: [illegible] ---
    simple_illegible = len(re.findall(r'\[illegible\]', text, re.IGNORECASE))
    if simple_illegible:
        gap_count += simple_illegible
        log.append(f"Found {simple_illegible} [illegible] marker(s)")
        text = re.sub(r'\[illegible\]', '', text, flags=re.IGNORECASE)

    # --- Pattern: [b....es] — partial reading with dots ---
    # Keep the visible letters, remove the dots and brackets.
    # e.g., [b....es] → bes (the dots represent unknown characters)
    partial_readings = re.findall(r'\[([a-zA-Z]*\.{2,}[a-zA-Z]*)\]', text)
    if partial_readings:
        for pr in partial_readings:
            dot_count = pr.count('.')
            illegible_chars += dot_count
        gap_count += len(partial_readings)
        log.append(f"Found {len(partial_readings)} partial reading(s) with dots: {partial_readings}")
        # Replace [b....es] with bes (remove dots, keep letters)
        text = re.sub(
            r'\[([a-zA-Z]*)(\.{2,})([a-zA-Z]*)\]',
            lambda m: m.group(1) + m.group(3),
            text
        )

    # --- Pattern: [...] — generic ellipsis gap ---
    # Must come last so we don't match the more specific patterns above.
    ellipsis_gaps = len(re.findall(r'\[\.\.\.+\]', text))
    if ellipsis_gaps:
        gap_count += ellipsis_gaps
        log.append(f"Found {ellipsis_gaps} [...] gap marker(s)")
        text = re.sub(r'\[\.\.\.+\]', '', text)

    return text, log, gap_count, illegible_chars


def normalize_whitespace(text):
    """
    Step 3: Clean up whitespace without altering content.

    - Collapse runs of multiple spaces into a single space
    - Trim leading/trailing whitespace from each line
    - Preserve line breaks (they may correspond to manuscript line breaks)

    We do NOT:
    - Remove blank lines (they may indicate paragraph/section breaks)
    - Lowercase anything
    - Remove punctuation
    - Alter any actual text content
    """
    log = []
    original = text

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.replace('\t', ' ')
        line = re.sub(r' {2,}', ' ', line)
        line = line.strip()
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    if text != original:
        log.append("Normalized whitespace (collapsed multiple spaces, trimmed lines)")

    return text, log


def normalize_text(text):
    """
    Run the full normalization pipeline.

    Order:
      1. Strip confidence markers ([?], [word?], {context: ...})
      2. Strip illegibility markers ([...], [illegible], [b....es], etc.)
      3. Normalize whitespace

    Preserved:
      - Original spelling (including archaic forms)
      - Punctuation (including early modern conventions)
      - Capitalization
      - Line breaks
      - Italics markers (*word*)
      - All orthographic features: u/v, i/j, long-s (ſ), thorns, doubled consonants, etc.
    """
    full_log = []

    # Step 0: Strip metadata headers (before ---)
    text, fm_log, _ = strip_frontmatter(text)
    full_log.extend(fm_log)

    text, conf_log, uncertain_count = strip_confidence_markers(text)
    full_log.extend(conf_log)

    text, illeg_log, gap_count, illegible_chars = strip_illegibility_markers(text)
    full_log.extend(illeg_log)

    text, ws_log = normalize_whitespace(text)
    full_log.extend(ws_log)

    return {
        'text': text,
        'log': full_log,
        'gap_count': gap_count,
        'uncertain_count': uncertain_count,
        'illegible_chars': illegible_chars,
    }


# ---------------------------------------------------------------------------
# CER COMPUTATION (using jiwer)
# ---------------------------------------------------------------------------
# jiwer is the standard library for WER/CER computation in speech and
# handwriting recognition research. It implements the same edit distance
# algorithms used in Transkribus benchmarks and HTR evaluation campaigns.
#
# We use jiwer.process_characters() which computes CER with full alignment
# details (substitutions, insertions, deletions). We pass our pre-normalized
# text and disable jiwer's internal transforms to preserve our custom
# normalization pipeline.
# ---------------------------------------------------------------------------


def compute_cer(reference_text, hypothesis_text):
    """
    Compute Character Error Rate between a reference and hypothesis transcription.

    CER = (Substitutions + Insertions + Deletions) / len(reference)

    This is the standard metric used in handwriting recognition evaluation
    (see: Romero et al. 2012, Sánchez et al. 2019, ICDAR HTR competitions).

    Coverage measures what fraction of the reference the transcriber actually
    attempted, based on illegibility markers in the hypothesis.

    Parameters:
        reference_text: Raw reference transcription (will be normalized)
        hypothesis_text: Raw hypothesis transcription (will be normalized)

    Returns:
        dict with all computed metrics and normalization logs
    """
    # Normalize both texts through the same pipeline
    ref_result = normalize_text(reference_text)
    hyp_result = normalize_text(hypothesis_text)

    ref_normalized = ref_result['text']
    hyp_normalized = hyp_result['text']

    ref_len = len(ref_normalized)
    hyp_len = len(hyp_normalized)

    # Compute CER using jiwer
    # We use process_characters() for detailed alignment,
    # with no additional transforms (our normalization already handles it)
    if ref_len == 0:
        cer = float('inf') if hyp_len > 0 else 0.0
        substitutions = 0
        insertions = hyp_len
        deletions = 0
    else:
        output = jiwer.process_characters(
            ref_normalized,
            hyp_normalized,
        )
        cer = output.cer
        substitutions = output.substitutions
        insertions = output.insertions
        deletions = output.deletions

    # Compute coverage
    # Coverage = (reference_chars - estimated_illegible_chars) / reference_chars
    illegible_chars = hyp_result['illegible_chars']
    if ref_len > 0:
        coverage = max(0.0, (ref_len - illegible_chars) / ref_len)
    else:
        coverage = 1.0 if illegible_chars == 0 else 0.0

    # Build normalization log
    normalization_log = []
    if ref_result['log']:
        normalization_log.append({"source": "reference", "actions": ref_result['log']})
    if hyp_result['log']:
        normalization_log.append({"source": "hypothesis", "actions": hyp_result['log']})

    cer_percent = f"{cer * 100:.2f}%"

    return {
        'reference_characters': ref_len,
        'hypothesis_characters': hyp_len,
        'substitutions': substitutions,
        'insertions': insertions,
        'deletions': deletions,
        'cer': round(cer, 6),
        'cer_percent': cer_percent,
        'coverage': round(coverage, 4),
        'gap_count': hyp_result['gap_count'],
        'uncertain_count': hyp_result['uncertain_count'],
        'normalization_log': normalization_log,
    }


# ---------------------------------------------------------------------------
# COMMAND-LINE INTERFACE
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Compute Character Error Rate (CER) between a reference transcription '
            'and a hypothesis transcription. Uses jiwer (the standard HTR/OCR '
            'evaluation library) for edit distance. Applies a deterministic '
            'normalization pipeline before comparison. Outputs JSON to stdout.'
        ),
        epilog=(
            'Examples:\n'
            '  python compute_cer.py reference.txt hypothesis.txt\n'
            '  python compute_cer.py reference.txt hypothesis.txt --raw\n'
            '  python compute_cer.py reference.txt hypothesis.txt --verbose\n'
            '\n'
            'Dependencies: pip install -r requirements.txt\n'
            '  (jiwer >= 3.0, numpy >= 1.24, scipy >= 1.10)\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'reference',
        help='Path to the reference (ground truth) transcription file',
    )
    parser.add_argument(
        'hypothesis',
        help='Path to the hypothesis (AI-generated) transcription file',
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Output only the CER number (decimal) instead of full JSON',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print normalization log and edit details to stderr',
    )

    args = parser.parse_args()

    # Read input files
    try:
        with open(args.reference, 'r', encoding='utf-8') as f:
            reference_text = f.read()
    except FileNotFoundError:
        print(f"Error: Reference file not found: {args.reference}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.hypothesis, 'r', encoding='utf-8') as f:
            hypothesis_text = f.read()
    except FileNotFoundError:
        print(f"Error: Hypothesis file not found: {args.hypothesis}", file=sys.stderr)
        sys.exit(1)

    # Compute CER
    result = compute_cer(reference_text, hypothesis_text)

    # Verbose output to stderr
    if args.verbose:
        print("=" * 60, file=sys.stderr)
        print("CER COMPUTATION — jiwer + custom normalization", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for entry in result['normalization_log']:
            print(f"\n[{entry['source'].upper()}]", file=sys.stderr)
            for action in entry['actions']:
                print(f"  - {action}", file=sys.stderr)
        if not result['normalization_log']:
            print("  (no normalization actions taken)", file=sys.stderr)
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"Reference characters:  {result['reference_characters']}", file=sys.stderr)
        print(f"Hypothesis characters: {result['hypothesis_characters']}", file=sys.stderr)
        print(f"Substitutions:         {result['substitutions']}", file=sys.stderr)
        print(f"Insertions:            {result['insertions']}", file=sys.stderr)
        print(f"Deletions:             {result['deletions']}", file=sys.stderr)
        print(f"CER:                   {result['cer_percent']}", file=sys.stderr)
        print(f"Coverage:              {result['coverage'] * 100:.1f}%", file=sys.stderr)
        print(f"Gap markers:           {result['gap_count']}", file=sys.stderr)
        print(f"Uncertain markers:     {result['uncertain_count']}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    # Output
    if args.raw:
        print(result['cer'])
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
