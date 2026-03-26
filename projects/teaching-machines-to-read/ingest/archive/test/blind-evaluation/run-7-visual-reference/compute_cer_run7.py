#!/usr/bin/env python3
"""
Compute Character Error Rate (CER) for Run 7 blind transcription evaluation.
Uses Levenshtein edit distance at the character level.

Follows the same normalization approach as Run 6 (compute_cer.py).

Two CER metrics reported:
1. "Full CER" - standard CER comparing blind text (with [...] removed) against
   full reference. Penalizes for unread sections.
2. "Attempted CER" - CER on text the agent actually attempted, excluding [...]
   sections via word-level alignment.
"""

import re
import sys
from datetime import date


def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance with backtrace for S/I/D counts."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],      # deletion from s1
                    dp[i][j-1],      # insertion into s1
                    dp[i-1][j-1]     # substitution
                )

    # Backtrace
    i, j = m, n
    subs, ins, dels = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            ins += 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            dels += 1
            i -= 1
        else:
            break

    return dp[m][n], subs, ins, dels


def levenshtein_distance_simple(s1, s2):
    """Just return the distance, no backtrace."""
    m, n = len(s1), len(s2)
    if m == 0:
        return n
    if n == 0:
        return m
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]


def extract_blind_content(text):
    """Extract content between header separator and Confidence Notes."""
    lines = text.split('\n')
    content_lines = []
    in_content = False
    separator_count = 0
    for line in lines:
        if '======' in line:
            separator_count += 1
            if separator_count == 1:
                in_content = True
            elif separator_count >= 2:
                break
            continue
        if in_content:
            # Also stop at "Confidence Notes" line
            if line.strip() == 'Confidence Notes':
                break
            content_lines.append(line)
    return '\n'.join(content_lines)


def normalize_blind_markers(text):
    """Normalize blind text, keeping [...] as ILLEGIBLE token."""
    content = text

    # Strip section labels
    content = re.sub(r'\[LEFT PAGE[^\]]*\]', '', content)
    content = re.sub(r'\[RIGHT PAGE[^\]]*\]', '', content)
    content = re.sub(r'\[RIGHT COLUMN[^\]]*\]', '', content)
    content = re.sub(r'\[Passage largely illegible[^\]]*\]', '', content)
    content = re.sub(r'\[LEFT PAGE BOTTOM[^\]]*\]', '', content)
    content = re.sub(r'\[BOTTOM OF RIGHT PAGE[^\]]*\]', '', content)
    content = re.sub(r'\[Bottom portion[^\]]*\]', '', content)
    content = re.sub(r'\[Top of page[^\]]*\]', '', content)

    # Strip strikethrough
    content = re.sub(r'~~(.*?)~~', r'\1', content)

    # Strip italic markers
    content = re.sub(r'\*([^*]+)\*', r'\1', content)

    # Replace [...] / [....] / [......] with ILLEGIBLE token BEFORE stripping other brackets
    content = re.sub(r'\[\.{2,}\]', ' ILLEGIBLE ', content)

    # Strip decorative dot patterns (AFTER [...] conversion)
    content = re.sub(r'\.{3,}', '', content)
    content = re.sub(r'\.\s+\.\s+\.\s+\.[\s.]*', '', content)

    # Strip confidence markers [word?] -> word
    content = re.sub(r'\[([^\]]*?)\?\]', r'\1', content)

    # Strip remaining editorial brackets [b] -> b, etc.
    content = re.sub(r'\[([^\]]*?)\]', r'\1', content)

    return content


def normalize_reference(text):
    """Normalize reference transcription."""
    lines = text.split('\n')
    content_lines = []
    past_header = False
    for line in lines:
        if line.startswith('---'):
            past_header = True
            continue
        if past_header:
            content_lines.append(line)

    content = '\n'.join(content_lines)

    # Strip {page numbers}
    content = re.sub(r'\{[^}]*\}', '', content)

    # Handle [...] / [.....] in reference
    content = re.sub(r'\[\.+\]', '', content)

    # Strip editorial brackets
    content = re.sub(r'\[([^\]]*?)\]', r'\1', content)

    # Strip superscript ^
    content = re.sub(r'\^', '', content)

    return content


def clean_whitespace(text):
    """Collapse whitespace."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def word_level_align(blind_words, ref_words):
    """Word-level Levenshtein alignment."""
    m, n = len(blind_words), len(ref_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if blind_words[i-1] == ref_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    # Backtrace
    i, j = m, n
    aligned = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and blind_words[i-1] == ref_words[j-1]:
            aligned.append(('match', blind_words[i-1], ref_words[j-1]))
            i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            aligned.append(('sub', blind_words[i-1], ref_words[j-1]))
            i -= 1; j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            aligned.append(('ins', '', ref_words[j-1]))
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            aligned.append(('del', blind_words[i-1], ''))
            i -= 1
        else:
            break

    aligned.reverse()
    return aligned


def compute_attempted_cer(blind_with_markers, ref_text):
    """Compute CER only on text the agent attempted to read."""
    blind_words = blind_with_markers.split()
    ref_words = ref_text.split()

    aligned = word_level_align(blind_words, ref_words)

    attempted_blind_words = []
    attempted_ref_words = []

    for op, bw, rw in aligned:
        if bw == 'ILLEGIBLE':
            continue
        if op == 'match':
            attempted_blind_words.append(bw)
            attempted_ref_words.append(rw)
        elif op == 'sub':
            attempted_blind_words.append(bw)
            attempted_ref_words.append(rw)
        elif op == 'ins':
            attempted_ref_words.append(rw)
        elif op == 'del':
            attempted_blind_words.append(bw)

    attempted_blind = ' '.join(attempted_blind_words)
    attempted_ref = ' '.join(attempted_ref_words)

    dist, subs, ins, dels = levenshtein_distance(attempted_blind, attempted_ref)
    ref_len = len(attempted_ref)
    cer = dist / ref_len if ref_len > 0 else 0

    return {
        'attempted_blind': attempted_blind,
        'attempted_ref': attempted_ref,
        'distance': dist,
        'substitutions': subs,
        'insertions': ins,
        'deletions': dels,
        'ref_length': ref_len,
        'blind_length': len(attempted_blind),
        'cer': cer,
        'alignment': aligned,
        'illegible_count': sum(1 for op, bw, rw in aligned if bw == 'ILLEGIBLE'),
    }


def categorize_word_error(blind_word, ref_word):
    """Categorize a word-level substitution error."""
    b = blind_word.lower()
    r = ref_word.lower()

    b_stripped = re.sub(r'[^\w]', '', b)
    r_stripped = re.sub(r'[^\w]', '', r)

    # Capitalization only
    if b == r and blind_word != ref_word:
        return 'capitalization'

    # u/v convention
    if b.replace('u', 'v') == r.replace('u', 'v') or b.replace('v', 'u') == r.replace('v', 'u'):
        return 'uv_convention'

    # Terminal e
    if b + 'e' == r or b == r + 'e':
        return 'terminal_e'
    if b_stripped + 'e' == r_stripped or b_stripped == r_stripped + 'e':
        return 'terminal_e'

    # Double letter omission/insertion
    def collapse_doubles(s):
        return re.sub(r'(.)\1', r'\1', s)
    if collapse_doubles(b) == collapse_doubles(r):
        return 'double_letter'

    # Punctuation difference only
    if b_stripped == r_stripped:
        return 'punctuation'

    # Word segmentation (= signs indicating line breaks)
    if '=' in blind_word or '=' in ref_word:
        return 'word_segmentation'

    # Close match (1-2 char difference) = likely letterform misreading
    char_dist = levenshtein_distance_simple(b, r)
    if char_dist <= 2 and len(r) > 2:
        return 'letterform_misreading'

    # Significantly different = hallucination or major misreading
    if char_dist > max(len(r) * 0.5, 3):
        return 'hallucination'

    return 'other_spelling'


def main():
    manuscripts = [
        {
            'name': 'Henslow MS688',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-run7/henslow-transcription-final.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/henslow-ms688/test-page-reference.txt',
        },
        {
            'name': 'Sedley MS534',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-run7/sedley-transcription-final.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/sedley-ms534/test-page-reference.txt',
        },
        {
            'name': 'Bulkeley MS169',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-run7/bulkeley-transcription-final.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/bulkeley-ms169/test-page-reference.txt',
        },
        {
            'name': 'Brumwich MS160',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-run7/brumwich-transcription-final.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/brumwich-ms160/test-page-reference.txt',
        },
        {
            'name': 'Jane Jackson MS373',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-run7/jane-jackson-transcription-final.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/jane-jackson-ms-373/page-20-reference.txt',
        },
    ]

    results = []
    full_results = []

    for ms in manuscripts:
        with open(ms['blind'], 'r') as f:
            blind_raw = f.read()
        with open(ms['ref'], 'r') as f:
            ref_raw = f.read()

        # Extract and normalize
        blind_content = extract_blind_content(blind_raw)
        blind_with_markers = normalize_blind_markers(blind_content)
        blind_with_markers = clean_whitespace(blind_with_markers)

        ref_norm = normalize_reference(ref_raw)
        ref_final = clean_whitespace(ref_norm)

        # Full CER (blind with ILLEGIBLE removed vs full reference)
        blind_no_illegible = blind_with_markers.replace('ILLEGIBLE', ' ')
        blind_no_illegible = clean_whitespace(blind_no_illegible)
        full_dist, full_subs, full_ins, full_dels = levenshtein_distance(blind_no_illegible, ref_final)
        full_cer = full_dist / len(ref_final) if len(ref_final) > 0 else 0

        full_results.append({
            'name': ms['name'],
            'distance': full_dist,
            'ref_length': len(ref_final),
            'blind_length': len(blind_no_illegible),
            'cer': full_cer,
            'subs': full_subs,
            'ins': full_ins,
            'dels': full_dels,
        })

        # Attempted CER (excluding [...] sections)
        attempted = compute_attempted_cer(blind_with_markers, ref_final)
        attempted['name'] = ms['name']
        attempted['full_ref_length'] = len(ref_final)
        attempted['full_blind_length'] = len(blind_no_illegible)
        attempted['illegible_markers'] = blind_with_markers.count('ILLEGIBLE')

        results.append(attempted)

    # =========================================================================
    # BUILD REPORT
    # =========================================================================
    report = []
    report.append("=" * 80)
    report.append("BLIND TRANSCRIPTION EVALUATION REPORT -- RUN 7")
    report.append("Alphabet-First Method with Vocabulary Verification")
    report.append(f"Date: {date.today().isoformat()}")
    report.append("=" * 80)
    report.append("")

    report.append("METHOD")
    report.append("-" * 80)
    report.append("Run 7 uses the alphabet-first transcription method with vocabulary")
    report.append("verification (same methodology as Run 6). The transcription agent:")
    report.append("  1. Built a hand-specific alphabet from the manuscript image")
    report.append("  2. Transcribed the page using that alphabet + paleography guide")
    report.append("  3. Verified readings against a vocabulary reference of attested")
    report.append("     early modern recipe terms (~19K words from 40 sources)")
    report.append("")
    report.append("CER = (Substitutions + Insertions + Deletions) / Total Reference Characters")
    report.append("Computed using character-level Levenshtein edit distance.")
    report.append("")
    report.append("TWO CER METRICS ARE REPORTED:")
    report.append("")
    report.append("  1. FULL CER: Standard CER comparing blind text (with [...] removed)")
    report.append("     against the full reference. Penalizes for unread sections.")
    report.append("")
    report.append("  2. ATTEMPTED CER: CER computed only on text the agent attempted to read.")
    report.append("     [...] markers are aligned with reference words and those sections")
    report.append("     are excluded from both sides. This measures accuracy of what was")
    report.append("     actually transcribed.")
    report.append("")
    report.append("For manuscripts with few/no [...] markers, these are nearly identical.")
    report.append("For manuscripts with heavy [...] usage, they differ substantially.")
    report.append("")
    report.append("Normalization applied to blind text:")
    report.append("  - Headers, confidence notes, and metadata stripped")
    report.append("  - Decorative dot patterns stripped")
    report.append("  - Confidence markers [word?] -> word")
    report.append("  - Italic markers *letters* -> letters")
    report.append("  - Section labels stripped ([LEFT PAGE - VERSO], etc.)")
    report.append("  - [...] illegibility markers handled via alignment exclusion")
    report.append("")
    report.append("Normalization applied to reference text:")
    report.append("  - Source metadata header stripped")
    report.append("  - Editorial brackets stripped ([er] -> er, etc.)")
    report.append("  - Superscript markers ^ stripped")
    report.append("  - Page numbers in braces {6} stripped")
    report.append("  - Whitespace normalized")
    report.append("")

    # =========================================================================
    # INDIVIDUAL RESULTS
    # =========================================================================
    report.append("=" * 80)
    report.append("INDIVIDUAL MANUSCRIPT RESULTS")
    report.append("=" * 80)

    total_attempted_dist = 0
    total_attempted_ref = 0
    total_full_dist = 0
    total_full_ref = 0

    for i, (r, fr) in enumerate(zip(results, full_results)):
        total_attempted_dist += r['distance']
        total_attempted_ref += r['ref_length']
        total_full_dist += fr['distance']
        total_full_ref += fr['ref_length']

        report.append("")
        report.append(f"--- {r['name']} ---")
        report.append("")
        report.append(f"  [...] markers in transcription: {r['illegible_markers']}")
        report.append(f"  Coverage: {r['ref_length']}/{r['full_ref_length']} reference chars " +
                      f"({r['ref_length']/r['full_ref_length']*100:.1f}% of page attempted)")
        report.append("")
        report.append(f"  FULL CER (vs entire reference):")
        report.append(f"    Reference length:  {fr['ref_length']} characters")
        report.append(f"    Blind length:      {fr['blind_length']} characters")
        report.append(f"    Edit distance:     {fr['distance']}")
        report.append(f"      Substitutions:   {fr['subs']}")
        report.append(f"      Insertions:      {fr['ins']}")
        report.append(f"      Deletions:       {fr['dels']}")
        report.append(f"    CER:               {fr['cer']*100:.2f}%")
        report.append("")
        report.append(f"  ATTEMPTED CER (only on attempted text):")
        report.append(f"    Reference length:  {r['ref_length']} characters")
        report.append(f"    Blind length:      {r['blind_length']} characters")
        report.append(f"    Edit distance:     {r['distance']}")
        report.append(f"      Substitutions:   {r['substitutions']}")
        report.append(f"      Insertions:      {r['insertions']}")
        report.append(f"      Deletions:       {r['deletions']}")
        report.append(f"    CER:               {r['cer']*100:.2f}%")
        report.append("")

        # Error categorization from alignment
        alignment = r['alignment']
        error_categories = {}
        error_examples = {}

        for op, bw, rw in alignment:
            if bw == 'ILLEGIBLE':
                continue
            if op == 'sub':
                cat = categorize_word_error(bw, rw)
                error_categories[cat] = error_categories.get(cat, 0) + 1
                if cat not in error_examples:
                    error_examples[cat] = []
                error_examples[cat].append(f'"{bw}" vs ref "{rw}"')
            elif op == 'ins':
                error_categories['missing_word'] = error_categories.get('missing_word', 0) + 1
                if 'missing_word' not in error_examples:
                    error_examples['missing_word'] = []
                error_examples['missing_word'].append(f'(missing) vs ref "{rw}"')
            elif op == 'del':
                error_categories['extra_word'] = error_categories.get('extra_word', 0) + 1
                if 'extra_word' not in error_examples:
                    error_examples['extra_word'] = []
                error_examples['extra_word'].append(f'"{bw}" (not in ref)')

        if error_categories:
            report.append(f"  Word-level error categorization:")
            for cat, count in sorted(error_categories.items(), key=lambda x: -x[1]):
                report.append(f"    {cat}: {count}")
                if cat in error_examples:
                    for ex in error_examples[cat][:8]:
                        report.append(f"      {ex}")
            report.append("")

        # Show sample text
        report.append(f"  Attempted blind text (first 300 chars):")
        report.append(f"    {r['attempted_blind'][:300]}")
        report.append(f"  Attempted reference text (first 300 chars):")
        report.append(f"    {r['attempted_ref'][:300]}")
        report.append("")

    # =========================================================================
    # OVERALL RESULTS
    # =========================================================================
    overall_attempted_cer = total_attempted_dist / total_attempted_ref if total_attempted_ref > 0 else 0
    overall_full_cer = total_full_dist / total_full_ref if total_full_ref > 0 else 0

    report.append("=" * 80)
    report.append("OVERALL RESULTS")
    report.append("=" * 80)
    report.append(f"  Full CER (all text):             {overall_full_cer*100:.2f}%")
    report.append(f"    Total edit distance:            {total_full_dist}")
    report.append(f"    Total reference chars:          {total_full_ref}")
    report.append("")
    report.append(f"  Attempted CER (attempted only):  {overall_attempted_cer*100:.2f}%")
    report.append(f"    Total edit distance:            {total_attempted_dist}")
    report.append(f"    Total reference chars:          {total_attempted_ref}")
    report.append("")

    # =========================================================================
    # COMPARISON TABLE -- ALL RUNS
    # =========================================================================
    report.append("=" * 80)
    report.append("COMPARISON ACROSS ALL RUNS (1-7)")
    report.append("=" * 80)
    report.append("")
    report.append("Note: Runs 1-5 used a single CER metric. Runs 6-7 report both Full and")
    report.append("Attempted CER. The 'Full CER' column is comparable across all runs.")
    report.append("'Best Previous' shows the best CER achieved in Runs 1-6 for each manuscript.")
    report.append("")

    run7_full = {fr['name']: fr['cer']*100 for fr in full_results}
    run7_attempted = {r['name']: r['cer']*100 for r in results}

    header = f"{'Manuscript':<22} {'Run 1':>8} {'Run 2':>8} {'Run 3':>8} {'Run 4':>8} {'Run 5':>8} {'Run 6':>8} {'R7 Full':>8} {'R7 Attm':>8} {'Best<7':>8}"
    report.append(header)
    report.append("-" * len(header))

    # Previous run data (Full CER values)
    table_data = [
        ('Henslow MS688',      '~11.3%', '~12%',   '6.12%',  '4.96%',  '5.38%',  '3.80%',  3.80),
        ('Sedley MS534',       '~15.8%', '~21%',   'N/A',    '15.13%', '16.55%', '17.05%', 15.13),
        ('Bulkeley MS169',     '~22.8%', '~18%',   'N/A',    '18.70%', '20.90%', '16.21%', 16.21),
        ('Brumwich MS160',     '~96.1%', '~93%',   'N/A',    '9.30%',  '50.62%', '31.09%', 9.30),
        ('Jane Jackson MS373', '~95.6%', '~95%',   'N/A',    '77.41%', '46.85%', '61.72%', 46.85),
    ]

    for ms_name, r1, r2, r3, r4, r5, r6, best_prev in table_data:
        r7f = f"{run7_full.get(ms_name, 0):.2f}%"
        r7a = f"{run7_attempted.get(ms_name, 0):.2f}%"
        bp = f"{best_prev:.2f}%"
        report.append(f"{ms_name:<22} {r1:>8} {r2:>8} {r3:>8} {r4:>8} {r5:>8} {r6:>8} {r7f:>8} {r7a:>8} {bp:>8}")

    report.append("")

    # =========================================================================
    # RUN 7 vs BEST PREVIOUS
    # =========================================================================
    report.append("=" * 80)
    report.append("RUN 7 vs BEST PREVIOUS RESULT (Full CER)")
    report.append("=" * 80)
    report.append("")

    best_previous = {
        'Henslow MS688': (3.80, 'Run 6'),
        'Sedley MS534': (15.13, 'Run 4'),
        'Bulkeley MS169': (16.21, 'Run 6'),
        'Brumwich MS160': (9.30, 'Run 4'),
        'Jane Jackson MS373': (46.85, 'Run 5'),
    }

    improvements = 0
    regressions = 0
    roughly_same = 0

    for fr in full_results:
        r7_val = fr['cer'] * 100
        prev_val, prev_run = best_previous.get(fr['name'], (0, '?'))
        diff = r7_val - prev_val
        if diff < -0.5:
            direction = "IMPROVED"
            improvements += 1
        elif diff > 0.5:
            direction = "WORSE"
            regressions += 1
        else:
            direction = "~SAME"
            roughly_same += 1
        report.append(f"  {fr['name']}:")
        report.append(f"    Run 7: {r7_val:.2f}%  vs  Best previous: {prev_val:.2f}% ({prev_run})")
        report.append(f"    Difference: {diff:+.2f}pp  ({direction})")
        report.append("")

    report.append(f"  Summary: {improvements} improved, {roughly_same} roughly same, {regressions} worse")
    report.append("")

    # =========================================================================
    # RUN 7 vs RUN 6 (same methodology)
    # =========================================================================
    report.append("=" * 80)
    report.append("RUN 7 vs RUN 6 (same methodology, tests reproducibility)")
    report.append("=" * 80)
    report.append("")

    run6_full_cers = {
        'Henslow MS688': 3.80,
        'Sedley MS534': 17.05,
        'Bulkeley MS169': 16.21,
        'Brumwich MS160': 31.09,
        'Jane Jackson MS373': 61.72,
    }

    for fr in full_results:
        r7_val = fr['cer'] * 100
        r6_val = run6_full_cers.get(fr['name'], 0)
        diff = r7_val - r6_val
        if diff < -0.5:
            direction = "IMPROVED"
        elif diff > 0.5:
            direction = "WORSE"
        else:
            direction = "~SAME"
        report.append(f"  {fr['name']}: R7 {r7_val:.2f}% vs R6 {r6_val:.2f}% ({direction}, {diff:+.2f}pp)")

    report.append("")

    # =========================================================================
    # DETAILED ANALYSIS BY MANUSCRIPT
    # =========================================================================
    report.append("=" * 80)
    report.append("DETAILED ANALYSIS BY MANUSCRIPT")
    report.append("=" * 80)
    report.append("")

    for i, (r, fr) in enumerate(zip(results, full_results)):
        r7_full = fr['cer'] * 100
        r7_att = r['cer'] * 100
        prev_val, prev_run = best_previous.get(r['name'], (0, '?'))

        report.append(f"--- {r['name']} ---")
        report.append("")
        report.append(f"  Full CER: {r7_full:.2f}%  |  Attempted CER: {r7_att:.2f}%")
        report.append(f"  [...] markers: {r['illegible_markers']}")
        coverage = r['ref_length'] / r['full_ref_length'] * 100
        report.append(f"  Page coverage: {coverage:.1f}%")
        report.append(f"  Best previous: {prev_val:.2f}% ({prev_run})")
        diff = r7_full - prev_val
        report.append(f"  vs best previous: {diff:+.2f}pp")
        report.append("")

        # Manuscript-specific commentary
        if r['name'] == 'Henslow MS688':
            report.append("  Commentary:")
            report.append("  The easiest manuscript (large, clear secretary hand). Minimal [...]")
            report.append("  markers expected. This is the benchmark test -- consistently the best")
            report.append("  performing manuscript across all runs. The Run 6 result of 3.80%")
            report.append("  was close to the Transkribus Egerton benchmark (~3% CER).")
            if r7_full < 3.80:
                report.append(f"  NEW BEST RESULT: {r7_full:.2f}% -- surpasses Run 6's 3.80%.")
            elif abs(r7_full - 3.80) < 0.5:
                report.append(f"  Result ({r7_full:.2f}%) is consistent with Run 6 (3.80%), confirming")
                report.append("  reproducibility of the method on this manuscript.")
            else:
                report.append(f"  Result ({r7_full:.2f}%) differs from Run 6 (3.80%), indicating")
                report.append("  variability in the method even on this legible manuscript.")

        elif r['name'] == 'Sedley MS534':
            report.append("  Commentary:")
            report.append("  Clear italic hand, dense text with abbreviations. Two-page opening.")
            report.append("  Main challenge: abbreviations and compressed spacing.")
            report.append("  Run 4 achieved the previous best (15.13%).")
            if r7_full < 15.13:
                report.append(f"  NEW BEST RESULT: {r7_full:.2f}%.")
            else:
                report.append(f"  Result: {r7_full:.2f}% vs best 15.13% (Run 4).")

        elif r['name'] == 'Bulkeley MS169':
            report.append("  Commentary:")
            report.append("  Secretary hand, moderate difficulty. Herbal/medical text about lavender.")
            report.append("  Run 6 achieved the previous best (16.21%).")
            if r7_full < 16.21:
                report.append(f"  NEW BEST RESULT: {r7_full:.2f}%.")
            else:
                report.append(f"  Result: {r7_full:.2f}% vs best 16.21% (Run 6).")

        elif r['name'] == 'Brumwich MS160':
            report.append("  Commentary:")
            report.append("  Very difficult manuscript. Small, closely-spaced hand with water damage.")
            report.append("  Two-page opening. Run 4 achieved the previous best (9.30%) but with")
            report.append("  a different methodology. The alphabet-first method tends to make the")
            report.append("  agent more conservative on this manuscript (more [...] markers).")
            report.append(f"  [{r['illegible_markers']}] illegible markers indicate the agent's")
            report.append("  honesty about what it cannot read.")

        elif r['name'] == 'Jane Jackson MS373':
            report.append("  Commentary:")
            report.append("  Most difficult manuscript. Compact hand with severe water damage.")
            report.append("  Two-page opening. Run 5 achieved the previous best (46.85%).")
            report.append("  High density of [...] markers expected. This manuscript likely")
            report.append("  requires higher-resolution imaging for meaningful improvement.")

        report.append("")

    # =========================================================================
    # BENCHMARKS
    # =========================================================================
    report.append("=" * 80)
    report.append("BENCHMARK COMPARISON")
    report.append("=" * 80)
    report.append("  < 1% CER  = Very good")
    report.append("  < 5% CER  = Usable for most research purposes")
    report.append("  ~3% CER   = Transkribus Egerton model (best for English secretary hand)")
    report.append("  5-10%     = Moderate (needs review)")
    report.append("  10-20%    = Poor (heavy editing needed)")
    report.append("  > 20%     = Not usable (requires retranscription)")
    report.append("")

    for fr, r in zip(full_results, results):
        cer_pct = fr['cer'] * 100
        att_cer = r['cer'] * 100
        if cer_pct < 1:
            quality = "VERY GOOD"
        elif cer_pct < 5:
            quality = "USABLE (research quality)"
        elif cer_pct < 10:
            quality = "MODERATE (needs review)"
        elif cer_pct < 20:
            quality = "POOR (heavy editing needed)"
        else:
            quality = "NOT USABLE (requires retranscription)"

        coverage = r['ref_length'] / r['full_ref_length'] * 100
        report.append(f"  {fr['name']}:")
        report.append(f"    Full CER: {cer_pct:.2f}% -- {quality}")
        report.append(f"    Attempted CER: {att_cer:.2f}% (on {coverage:.0f}% of page)")
        report.append("")

    report.append(f"  Overall Full CER: {overall_full_cer*100:.2f}%")
    report.append(f"  Overall Attempted CER: {overall_attempted_cer*100:.2f}%")
    report.append("")

    # =========================================================================
    # KEY FINDINGS
    # =========================================================================
    report.append("=" * 80)
    report.append("KEY FINDINGS")
    report.append("=" * 80)
    report.append("")

    # Determine new bests
    new_bests = []
    for fr in full_results:
        r7_val = fr['cer'] * 100
        prev_val, prev_run = best_previous.get(fr['name'], (0, '?'))
        if r7_val < prev_val - 0.5:
            new_bests.append(fr['name'])

    if new_bests:
        report.append(f"New best CER achieved for: {', '.join(new_bests)}")
    else:
        report.append("No new best CER results in this run.")
    report.append("")

    report.append("REPRODUCIBILITY:")
    report.append("Run 7 uses the same methodology as Run 6 (alphabet-first + vocab")
    report.append("verification). Comparing the two runs tests whether the method produces")
    report.append("consistent results or shows significant stochastic variation.")
    report.append("")

    r6_cers = run6_full_cers
    for fr in full_results:
        r7_val = fr['cer'] * 100
        r6_val = r6_cers.get(fr['name'], 0)
        diff = abs(r7_val - r6_val)
        if diff < 1.0:
            report.append(f"  {fr['name']}: R7={r7_val:.2f}% vs R6={r6_val:.2f}% -- CONSISTENT (diff {diff:.2f}pp)")
        elif diff < 3.0:
            report.append(f"  {fr['name']}: R7={r7_val:.2f}% vs R6={r6_val:.2f}% -- MODERATE VARIATION (diff {diff:.2f}pp)")
        else:
            report.append(f"  {fr['name']}: R7={r7_val:.2f}% vs R6={r6_val:.2f}% -- HIGH VARIATION (diff {diff:.2f}pp)")

    report.append("")

    report.append("ACCURACY-COVERAGE TRADEOFF:")
    report.append("Manuscripts with many [...] markers show honest uncertainty. This")
    report.append("penalizes Full CER (because reference chars stay in the denominator)")
    report.append("but the Attempted CER shows the accuracy of what was actually read.")
    report.append("")

    for r in results:
        if r['illegible_markers'] > 5:
            coverage = r['ref_length'] / r['full_ref_length'] * 100
            report.append(f"  {r['name']}: {r['illegible_markers']} [...] markers, "
                         f"{coverage:.0f}% coverage, "
                         f"Attempted CER {r['cer']*100:.2f}%")
    report.append("")

    # Write report
    report_text = '\n'.join(report)

    output_path = '/Users/sarahbonanno/Desktop/blind-test-run7/run7-evaluation-report.txt'
    with open(output_path, 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()
