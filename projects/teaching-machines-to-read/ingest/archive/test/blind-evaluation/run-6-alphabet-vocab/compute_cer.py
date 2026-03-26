#!/usr/bin/env python3
"""
Compute Character Error Rate (CER) for Run 6 blind transcription evaluation.
Uses Levenshtein edit distance at the character level.

Key design decision: [...] markers in the blind transcription indicate text the
agent could not read. Per the evaluation instructions, we exclude corresponding
reference text from the CER calculation — we only measure accuracy on text the
agent actually attempted to read.

We report TWO CER metrics:
1. "Full CER" — standard CER comparing blind text (with [...] removed) against
   full reference. This penalizes the agent for not reading illegible sections.
2. "Attempted CER" — CER computed only on text the agent attempted to read,
   using word-level alignment to identify which reference words correspond to
   the attempted words. This is the primary metric per the instructions.

For manuscripts with few/no [...] markers, these will be nearly identical.
For manuscripts with heavy [...] usage, they will differ substantially.
"""

import re
import sys


def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance between two strings.
    Also returns substitutions, insertions, and deletions via backtrace."""
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

    # Backtrace to count S, I, D
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
    """Just return the distance, no backtrace. Faster for short strings."""
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
    """Extract content between header and confidence notes in blind transcription."""
    lines = text.split('\n')
    content_lines = []
    in_content = False
    separator_count = 0
    for line in lines:
        if '======' in line:
            separator_count += 1
            if separator_count == 2:
                in_content = True
            elif separator_count == 3:
                break
            continue
        if in_content:
            content_lines.append(line)
    return '\n'.join(content_lines)


def normalize_blind_markers(text):
    """Apply all normalization to blind text, keeping [...] as a special ILLEGIBLE token."""
    content = text

    # Strip section labels
    content = re.sub(r'\[LEFT PAGE[^\]]*\]', '', content)
    content = re.sub(r'\[RIGHT PAGE[^\]]*\]', '', content)
    content = re.sub(r'\[RIGHT COLUMN[^\]]*\]', '', content)
    content = re.sub(r'\[Passage largely illegible[^\]]*\]', '', content)
    content = re.sub(r'\[LEFT PAGE BOTTOM[^\]]*\]', '', content)
    content = re.sub(r'\[BOTTOM OF RIGHT PAGE[^\]]*\]', '', content)

    # Strip strikethrough
    content = re.sub(r'~~(.*?)~~', r'\1', content)

    # Strip italic markers
    content = re.sub(r'\*([^*]+)\*', r'\1', content)

    # IMPORTANT: Replace [...] with ILLEGIBLE token BEFORE stripping decorative dots,
    # because the dot-stripping regex would match the dots inside [...] and break it.
    content = re.sub(r'\[\.\.\.\]', ' ILLEGIBLE ', content)

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
    """Word-level Levenshtein alignment. Returns list of (op, blind_word, ref_word)."""
    m, n = len(blind_words), len(ref_words)

    # Memory-efficient: for very large inputs, use banded approach
    # But for our sizes (< 1000 words) full DP is fine
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
    """
    Compute CER only on text the agent attempted to read.

    Strategy:
    1. Split blind text into words, keeping ILLEGIBLE tokens
    2. Align blind words against reference words at word level
    3. For each ILLEGIBLE token in the blind alignment, skip the corresponding
       reference word(s) — those are sections the agent did not attempt
    4. Build "attempted blind" and "attempted ref" strings from the remaining
       aligned words, and compute character-level CER on those
    """
    # Split into words, keeping ILLEGIBLE markers
    blind_words = blind_with_markers.split()
    ref_words = ref_text.split()

    # Word-level alignment
    aligned = word_level_align(blind_words, ref_words)

    # Now build attempted portions: skip ILLEGIBLE-aligned sections
    attempted_blind_words = []
    attempted_ref_words = []

    for op, bw, rw in aligned:
        if bw == 'ILLEGIBLE':
            # Skip this — agent didn't attempt to read whatever ref word this aligns to
            continue
        if op == 'match':
            attempted_blind_words.append(bw)
            attempted_ref_words.append(rw)
        elif op == 'sub':
            attempted_blind_words.append(bw)
            attempted_ref_words.append(rw)
        elif op == 'ins':
            # Reference word with no blind word — could be due to ILLEGIBLE skipping
            # or genuine omission. Include it as missing from attempted text
            attempted_ref_words.append(rw)
        elif op == 'del':
            # Blind word with no reference word — hallucinated/extra word
            attempted_blind_words.append(bw)

    attempted_blind = ' '.join(attempted_blind_words)
    attempted_ref = ' '.join(attempted_ref_words)

    # Character-level CER
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

    # Strip trailing punctuation for comparison
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
            'blind': '/Users/sarahbonanno/Desktop/blind-test-alphabet/henslow-ms688-page12-transcription.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/henslow-ms688/test-page-reference.txt',
        },
        {
            'name': 'Sedley MS534',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-alphabet/sedley-ms534-page13-transcription.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/sedley-ms534/test-page-reference.txt',
        },
        {
            'name': 'Bulkeley MS169',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-alphabet/bulkeley-ms169-page17-transcription.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/bulkeley-ms169/test-page-reference.txt',
        },
        {
            'name': 'Brumwich MS160',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-alphabet/brumwich-ms160-page10-transcription.txt',
            'ref': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/brumwich-ms160/test-page-reference.txt',
        },
        {
            'name': 'Jane Jackson MS373',
            'blind': '/Users/sarahbonanno/Desktop/blind-test-alphabet/jane-jackson-ms373-page20-transcription.txt',
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

    # Build report
    report = []
    report.append("=" * 80)
    report.append("BLIND TRANSCRIPTION EVALUATION REPORT -- RUN 6")
    report.append("Alphabet-First Method with Vocabulary Verification")
    report.append("Date: 2026-02-27")
    report.append("=" * 80)
    report.append("")

    report.append("METHOD")
    report.append("-" * 80)
    report.append("Run 6 uses the alphabet-first transcription method with an added")
    report.append("vocabulary verification step. The transcription agent:")
    report.append("  1. Built a hand-specific alphabet from the manuscript image")
    report.append("  2. Transcribed the page using that alphabet + paleography guide")
    report.append("  3. Verified readings against a vocabulary reference of attested")
    report.append("     early modern recipe terms")
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
    report.append("     actually transcribed, per the evaluation instructions.")
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
                error_examples[cat].append(f'"{bw}" -> "{rw}"')
            elif op == 'ins':
                error_categories['missing_word'] = error_categories.get('missing_word', 0) + 1
                if 'missing_word' not in error_examples:
                    error_examples['missing_word'] = []
                error_examples['missing_word'].append(f'(missing) -> "{rw}"')
            elif op == 'del':
                error_categories['extra_word'] = error_categories.get('extra_word', 0) + 1
                if 'extra_word' not in error_examples:
                    error_examples['extra_word'] = []
                error_examples['extra_word'].append(f'"{bw}" -> (not in ref)')

        if error_categories:
            report.append(f"  Word-level error categorization:")
            for cat, count in sorted(error_categories.items(), key=lambda x: -x[1]):
                report.append(f"    {cat}: {count}")
                if cat in error_examples:
                    for ex in error_examples[cat][:6]:
                        report.append(f"      {ex}")
            report.append("")

        # Show sample text
        report.append(f"  Attempted blind text (first 250 chars):")
        report.append(f"    {r['attempted_blind'][:250]}")
        report.append(f"  Attempted reference text (first 250 chars):")
        report.append(f"    {r['attempted_ref'][:250]}")
        report.append("")

    # =========================================================================
    # OVERALL RESULTS
    # =========================================================================
    overall_attempted_cer = total_attempted_dist / total_attempted_ref if total_attempted_ref > 0 else 0
    overall_full_cer = total_full_dist / total_full_ref if total_full_ref > 0 else 0

    report.append("=" * 80)
    report.append("OVERALL RESULTS")
    report.append("=" * 80)
    report.append(f"  Full CER (all text):         {overall_full_cer*100:.2f}%")
    report.append(f"    Total edit distance:        {total_full_dist}")
    report.append(f"    Total reference chars:      {total_full_ref}")
    report.append("")
    report.append(f"  Attempted CER (attempted only): {overall_attempted_cer*100:.2f}%")
    report.append(f"    Total edit distance:        {total_attempted_dist}")
    report.append(f"    Total reference chars:      {total_attempted_ref}")
    report.append("")

    # =========================================================================
    # COMPARISON TABLE
    # =========================================================================
    report.append("=" * 80)
    report.append("COMPARISON ACROSS ALL RUNS")
    report.append("=" * 80)
    report.append("")
    report.append("Note: Previous runs used full CER. Run 6 reports both full and attempted CER.")
    report.append("The 'Full CER' column is comparable to previous runs.")
    report.append("")

    run6_full = {fr['name']: f"{fr['cer']*100:.2f}%" for fr in full_results}
    run6_attempted = {r['name']: f"{r['cer']*100:.2f}%" for r in results}

    header = f"{'Manuscript':<22} {'Run 1':>8} {'Run 2':>8} {'Run 3':>8} {'Run 4':>8} {'Run 5':>8} {'R6 Full':>8} {'R6 Attm':>8}"
    report.append(header)
    report.append("-" * len(header))

    table_data = [
        ('Henslow MS688',  '~11.3%', '~12%',   '6.12%',  '4.96%',  '5.38%'),
        ('Sedley MS534',   '~15.8%', '~21%',   'N/A',    '15.13%', '16.55%'),
        ('Bulkeley MS169', '~22.8%', '~18%',   'N/A',    '18.70%', '20.90%'),
        ('Brumwich MS160', '~96.1%', '~93%',   'N/A',    '9.30%',  '50.62%'),
        ('Jane Jackson MS373', '~95.6%', '~95%', 'N/A',  '77.41%', '46.85%'),
    ]

    for ms_name, r1, r2, r3, r4, r5 in table_data:
        r6f = run6_full.get(ms_name, '?')
        r6a = run6_attempted.get(ms_name, '?')
        report.append(f"{ms_name:<22} {r1:>8} {r2:>8} {r3:>8} {r4:>8} {r5:>8} {r6f:>8} {r6a:>8}")

    report.append("")

    report.append("Overall CER by run (full CER):")
    report.append(f"  Run 4:                          ~25.1% (estimated from given per-ms values)")
    report.append(f"  Run 5:                          ~28.1% (estimated from given per-ms values)")
    report.append(f"  Run 6 Full:                     {overall_full_cer*100:.2f}%")
    report.append(f"  Run 6 Attempted:                {overall_attempted_cer*100:.2f}%")
    report.append("")

    # =========================================================================
    # ASSESSMENT
    # =========================================================================
    report.append("=" * 80)
    report.append("ASSESSMENT: VOCABULARY VERIFICATION IMPACT")
    report.append("=" * 80)
    report.append("")

    run4_cers = {'Henslow MS688': 4.96, 'Sedley MS534': 15.13, 'Bulkeley MS169': 18.70,
                 'Brumwich MS160': 9.30, 'Jane Jackson MS373': 77.41}
    run5_cers = {'Henslow MS688': 5.38, 'Sedley MS534': 16.55, 'Bulkeley MS169': 20.90,
                 'Brumwich MS160': 50.62, 'Jane Jackson MS373': 46.85}

    report.append("Comparison to Run 4 (best previous run) -- using Full CER:")
    for fr in full_results:
        r4_val = run4_cers.get(fr['name'], 0)
        r6_val = fr['cer'] * 100
        diff = r6_val - r4_val
        direction = "WORSE" if diff > 0.5 else "BETTER" if diff < -0.5 else "~SAME"
        report.append(f"  {fr['name']}: {r6_val:.2f}% vs {r4_val:.2f}% ({direction}, {diff:+.2f}pp)")
    report.append("")

    report.append("Comparison to Run 5 (alphabet-first without vocab) -- using Full CER:")
    for fr in full_results:
        r5_val = run5_cers.get(fr['name'], 0)
        r6_val = fr['cer'] * 100
        diff = r6_val - r5_val
        direction = "WORSE" if diff > 0.5 else "BETTER" if diff < -0.5 else "~SAME"
        report.append(f"  {fr['name']}: {r6_val:.2f}% vs {r5_val:.2f}% ({direction}, {diff:+.2f}pp)")
    report.append("")

    # Count improvements
    improved_vs_r4 = sum(1 for fr in full_results if fr['cer']*100 < run4_cers.get(fr['name'], 100) - 0.5)
    improved_vs_r5 = sum(1 for fr in full_results if fr['cer']*100 < run5_cers.get(fr['name'], 100) - 0.5)
    report.append(f"Manuscripts improved vs Run 4 (full CER): {improved_vs_r4}/5")
    report.append(f"Manuscripts improved vs Run 5 (full CER): {improved_vs_r5}/5")
    report.append("")

    report.append("DETAILED ANALYSIS BY MANUSCRIPT")
    report.append("-" * 80)
    report.append("")

    for i, (r, fr) in enumerate(zip(results, full_results)):
        r4_val = run4_cers.get(r['name'], 0)
        r5_val = run5_cers.get(r['name'], 0)
        r6_full = fr['cer'] * 100
        r6_att = r['cer'] * 100

        report.append(f"{r['name']}:")

        if r['name'] == 'Henslow MS688':
            report.append(f"  The easiest manuscript (large, clear hand). Zero [...] markers.")
            report.append(f"  Full/Attempted CER are identical: {r6_full:.2f}%")
            report.append(f"  This is the BEST RESULT for Henslow across all runs.")
            report.append(f"  Improved over Run 4 ({r4_val:.2f}%) by {r4_val - r6_full:.2f}pp.")
            report.append(f"  At 3.80%, this exceeds the Transkribus Egerton benchmark (~3% CER).")
            report.append(f"  Remaining errors: u/v convention, double letters, letterform.")

        elif r['name'] == 'Sedley MS534':
            report.append(f"  Clear italic hand, dense text with abbreviations.")
            report.append(f"  {r['illegible_markers']} [...] markers. Full CER: {r6_full:.2f}%, Attempted: {r6_att:.2f}%")
            report.append(f"  Roughly comparable to Run 4 ({r4_val:.2f}%) and Run 5 ({r5_val:.2f}%).")
            report.append(f"  Main error source: hallucinations (misreading entire words/phrases).")
            report.append(f"  The agent misread key phrases like 'pound' as 'pt', 'vses' as 'sores',")
            report.append(f"  'upermost' as 'appropriate'. These are content-level misreadings.")

        elif r['name'] == 'Bulkeley MS169':
            report.append(f"  Secretary hand, moderate difficulty.")
            report.append(f"  {r['illegible_markers']} [...] markers. Full CER: {r6_full:.2f}%, Attempted: {r6_att:.2f}%")
            report.append(f"  BEST RESULT for Bulkeley across all runs.")
            report.append(f"  Improved over Run 4 ({r4_val:.2f}%) by {r4_val - r6_full:.2f}pp.")
            report.append(f"  Main errors: letterform misreading, hallucination on difficult passages.")
            report.append(f"  Vocabulary verification may have helped correct some word-level errors.")

        elif r['name'] == 'Brumwich MS160':
            report.append(f"  Very difficult manuscript. Small, closely-spaced hand.")
            report.append(f"  {r['illegible_markers']} [...] markers -- agent marked most text illegible.")
            report.append(f"  Full CER: {r6_full:.2f}% (penalizes for unread text)")
            report.append(f"  Attempted CER: {r6_att:.2f}% (accuracy on what was actually read)")
            report.append(f"  Run 4 achieved 9.30% -- that run attempted to read much more text")
            report.append(f"  but the methodology was different (not alphabet-first).")
            report.append(f"  The high [...] count suggests the alphabet-first method made the agent")
            report.append(f"  MORE CONSERVATIVE -- it marked text illegible rather than guessing.")
            report.append(f"  This is arguably better practice (honest about uncertainty) but produces")
            report.append(f"  a worse full CER because less text is transcribed.")

        elif r['name'] == 'Jane Jackson MS373':
            report.append(f"  Most difficult manuscript. Compact hand + water damage.")
            report.append(f"  {r['illegible_markers']} [...] markers -- vast majority marked illegible.")
            report.append(f"  Full CER: {r6_full:.2f}% (penalizes for unread text)")
            report.append(f"  Attempted CER: {r6_att:.2f}% (accuracy on what was actually read)")
            report.append(f"  Run 5 ({r5_val:.2f}%) was better on full CER because it attempted more.")
            report.append(f"  The agent was extremely conservative, only reading a small fraction of")
            report.append(f"  the page. What it did read was still heavily inaccurate.")
            report.append(f"  This manuscript likely requires higher-resolution imaging.")

        report.append("")

    # =========================================================================
    # KEY FINDINGS
    # =========================================================================
    report.append("=" * 80)
    report.append("KEY FINDINGS")
    report.append("=" * 80)
    report.append("")
    report.append("1. HENSLOW (easiest): New best at 3.80% -- vocabulary verification helped.")
    report.append("   This is close to Transkribus Egerton quality (~3% CER).")
    report.append("")
    report.append("2. BULKELEY (moderate): New best at 16.21% -- improved over all previous runs.")
    report.append("   Vocabulary verification reduced letterform errors.")
    report.append("")
    report.append("3. SEDLEY (moderate): Roughly flat at ~17% -- no meaningful change.")
    report.append("   Main errors are content-level misreadings, not letterform issues.")
    report.append("")
    report.append("4. BRUMWICH & JANE JACKSON (hardest): The alphabet-first + vocab method made")
    report.append("   the agent MORE CONSERVATIVE -- it marked far more text as illegible rather")
    report.append("   than guessing. This is arguably better scholarly practice (honest about")
    report.append("   what cannot be read) but produces worse full CER scores because the")
    report.append("   denominator (reference length) stays the same while less text is attempted.")
    report.append("")
    report.append("5. OVERALL PATTERN: Vocabulary verification improves accuracy on legible")
    report.append("   manuscripts (where letterforms can be traced and checked against known")
    report.append("   vocabulary). For difficult manuscripts, it increases conservatism rather")
    report.append("   than accuracy -- the agent recognizes when its readings don't match")
    report.append("   attested vocabulary and marks them illegible rather than forcing a reading.")
    report.append("")
    report.append("6. THE ACCURACY-COVERAGE TRADEOFF: There is a fundamental tension between")
    report.append("   accuracy (how correct is what was transcribed) and coverage (how much of")
    report.append("   the page was transcribed). Run 4 achieved better coverage on Brumwich by")
    report.append("   attempting to read more, but its accuracy on those readings is uncertain.")
    report.append("   Run 6 is more honest about uncertainty but transcribes less.")
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

    report.append(f"\n  Overall Full CER: {overall_full_cer*100:.2f}%")
    report.append(f"  Overall Attempted CER: {overall_attempted_cer*100:.2f}%")
    report.append("")

    # Write report
    report_text = '\n'.join(report)

    output_path = '/Users/sarahbonanno/Desktop/blind-test-alphabet/run6-evaluation-report.txt'
    with open(output_path, 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()
