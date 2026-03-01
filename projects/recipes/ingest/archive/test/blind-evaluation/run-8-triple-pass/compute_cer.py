#!/usr/bin/env python3
"""
Compute Character Error Rate (CER) for Run 8 blind transcription evaluation.
Triple-pass consensus method with vocabulary verification.

Uses the same CER methodology as Runs 4-7 for direct comparison.
"""

import re


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
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    i, j = m, n
    subs, ins, dels = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            subs += 1; i -= 1; j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            ins += 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            dels += 1; i -= 1
        else:
            break
    return dp[m][n], subs, ins, dels


def levenshtein_distance_simple(s1, s2):
    """Just return the distance, no backtrace."""
    m, n = len(s1), len(s2)
    if m == 0: return n
    if n == 0: return m
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


def extract_reconciliation_content(text):
    """Extract transcription content from a reconciliation final/consensus file.

    Format: header lines ending with ===... separator, then transcription text,
    optionally followed by VOCAB VERIFICATION CHANGES section.
    """
    lines = text.split('\n')
    content_lines = []
    past_header = False

    for line in lines:
        # Skip everything until we pass the === separator
        if '=====' in line:
            past_header = True
            continue
        if not past_header:
            continue
        # Stop at VOCAB VERIFICATION CHANGES section
        if line.strip().startswith('VOCAB VERIFICATION CHANGES'):
            break
        content_lines.append(line)

    return '\n'.join(content_lines)


def normalize_blind_markers(text):
    """Normalize blind text, keeping [...] as ILLEGIBLE token."""
    content = text

    # Strip section labels
    content = re.sub(r'\[Left page[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Right page[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[RIGHT COLUMN[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Passage largely illegible[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Passage heavily damaged[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Bottom portion[^\]]*\]', '', content, flags=re.IGNORECASE)

    # Strip strikethrough
    content = re.sub(r'~~(.*?)~~', r'\1', content)

    # Strip italic markers *letters* -> letters
    content = re.sub(r'\*([^*]+)\*', r'\1', content)

    # Replace [...] with ILLEGIBLE token BEFORE stripping decorative dots
    content = re.sub(r'\[\.\.\.\]', ' ILLEGIBLE ', content)

    # Strip decorative dot patterns (AFTER [...] conversion)
    content = re.sub(r'\.{3,}', '', content)
    content = re.sub(r'\.\s+\.\s+\.\s+\.[\s.]*', '', content)
    # Also handle spaced dots like ". . . ."
    content = re.sub(r'(?:\.\s+){2,}\.?', '', content)

    # Handle multi-option uncertainty markers [word1/word2/word3?] -> take first word
    content = re.sub(r'\[([^/\]]+)/[^\]]*\?\]', r'\1', content)

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

    if b == r and blind_word != ref_word:
        return 'capitalization'
    if b.replace('u', 'v') == r.replace('u', 'v') or b.replace('v', 'u') == r.replace('v', 'u'):
        return 'uv_convention'
    if b + 'e' == r or b == r + 'e':
        return 'terminal_e'
    if b_stripped + 'e' == r_stripped or b_stripped == r_stripped + 'e':
        return 'terminal_e'

    def collapse_doubles(s):
        return re.sub(r'(.)\1', r'\1', s)
    if collapse_doubles(b) == collapse_doubles(r):
        return 'double_letter'
    if b_stripped == r_stripped:
        return 'punctuation'
    if '=' in blind_word or '=' in ref_word:
        return 'word_segmentation'

    char_dist = levenshtein_distance_simple(b, r)
    if char_dist <= 2 and len(r) > 2:
        return 'letterform_misreading'
    if char_dist > max(len(r) * 0.5, 3):
        return 'hallucination'
    return 'other_spelling'


def main():
    base = '/Users/sarahbonanno/Desktop/blind-test-run8/reconciliation'
    ref_base = '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test'

    manuscripts = [
        {
            'name': 'Henslow MS688',
            'blind': f'{base}/henslow-final.txt',
            'ref': f'{ref_base}/henslow-ms688/test-page-reference.txt',
        },
        {
            'name': 'Sedley MS534',
            'blind': f'{base}/sedley-final.txt',
            'ref': f'{ref_base}/sedley-ms534/test-page-reference.txt',
        },
        {
            'name': 'Bulkeley MS169',
            'blind': f'{base}/bulkeley-final.txt',
            'ref': f'{ref_base}/bulkeley-ms169/test-page-reference.txt',
        },
        {
            'name': 'Brumwich MS160',
            'blind': f'{base}/brumwich-final.txt',
            'ref': f'{ref_base}/brumwich-ms160/test-page-reference.txt',
        },
        {
            'name': 'Jane Jackson MS373',
            # No -final.txt for Jane Jackson (no vocab changes), use consensus
            'blind': f'{base}/jane-jackson-consensus.txt',
            'ref': f'{ref_base}/jane-jackson-ms-373/page-20-reference.txt',
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
        blind_content = extract_reconciliation_content(blind_raw)
        blind_with_markers = normalize_blind_markers(blind_content)
        blind_with_markers = clean_whitespace(blind_with_markers)

        ref_norm = normalize_reference(ref_raw)
        ref_final = clean_whitespace(ref_norm)

        # Full CER
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

        # Attempted CER
        attempted = compute_attempted_cer(blind_with_markers, ref_final)
        attempted['name'] = ms['name']
        attempted['full_ref_length'] = len(ref_final)
        attempted['full_blind_length'] = len(blind_no_illegible)
        attempted['illegible_markers'] = blind_with_markers.count('ILLEGIBLE')
        results.append(attempted)

    # Build report
    report = []
    report.append("=" * 80)
    report.append("BLIND TRANSCRIPTION EVALUATION REPORT -- RUN 8")
    report.append("Triple-Pass Consensus Method with Vocabulary Verification")
    report.append("Date: 2026-02-28")
    report.append("=" * 80)
    report.append("")

    report.append("METHOD")
    report.append("-" * 80)
    report.append("Run 8 uses a triple-pass consensus approach inspired by EMROC triple-keying:")
    report.append("  1. Three independent agents each transcribed all 5 manuscripts using the")
    report.append("     alphabet-first method (Run 4 style — NO vocabulary list)")
    report.append("  2. A fourth reconciliation agent merged the three passes into a consensus")
    report.append("     reading using majority rule")
    report.append("  3. Vocabulary verification was applied ONLY to the final consensus")
    report.append("")
    report.append("This combines Run 4's confident reading (no vocab distraction during")
    report.append("transcription) with Run 6's vocab verification (on a strong consensus base).")
    report.append("")
    report.append("CER = (Substitutions + Insertions + Deletions) / Total Reference Characters")
    report.append("")
    report.append("TWO CER METRICS ARE REPORTED:")
    report.append("  1. FULL CER: vs entire reference, penalizes for unread sections")
    report.append("  2. ATTEMPTED CER: only on text actually transcribed")
    report.append("")

    # Individual results
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

        # Error categorization
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

        # Sample text
        report.append(f"  Attempted blind text (first 250 chars):")
        report.append(f"    {r['attempted_blind'][:250]}")
        report.append(f"  Attempted reference text (first 250 chars):")
        report.append(f"    {r['attempted_ref'][:250]}")
        report.append("")

    # Overall results
    overall_attempted_cer = total_attempted_dist / total_attempted_ref if total_attempted_ref > 0 else 0
    overall_full_cer = total_full_dist / total_full_ref if total_full_ref > 0 else 0

    report.append("=" * 80)
    report.append("OVERALL RESULTS")
    report.append("=" * 80)
    report.append(f"  Full CER (all text):              {overall_full_cer*100:.2f}%")
    report.append(f"    Total edit distance:             {total_full_dist}")
    report.append(f"    Total reference chars:           {total_full_ref}")
    report.append("")
    report.append(f"  Attempted CER (attempted only):   {overall_attempted_cer*100:.2f}%")
    report.append(f"    Total edit distance:             {total_attempted_dist}")
    report.append(f"    Total reference chars:           {total_attempted_ref}")
    report.append("")

    # Comparison table
    report.append("=" * 80)
    report.append("COMPARISON ACROSS ALL RUNS (Full CER)")
    report.append("=" * 80)
    report.append("")

    run8_full = {fr['name']: fr['cer']*100 for fr in full_results}
    run8_attempted = {r['name']: r['cer']*100 for r in results}

    header = f"{'Manuscript':<22} {'R1':>7} {'R2':>7} {'R3':>7} {'R4':>7} {'R5':>7} {'R6':>7} {'R7':>7} {'R8':>7} {'Best':>7}"
    report.append(header)
    report.append("-" * len(header))

    table_data = [
        ('Henslow MS688',      11.3, 12.0,  6.12,  4.96, 5.38,  3.80,  7.59),
        ('Sedley MS534',       15.8, 21.0,  None,  15.13, 16.55, 16.96, 16.42),
        ('Bulkeley MS169',     22.8, 18.0,  None,  18.70, 20.90, 16.21, 18.29),
        ('Brumwich MS160',     96.1, 93.0,  None,   9.30, 50.62, 69.29, 62.49),
        ('Jane Jackson MS373', 95.6, 95.0,  None,  77.41, 46.85, 80.62, 67.22),
    ]

    for ms_name, r1, r2, r3, r4, r5, r6, r7 in table_data:
        r8 = run8_full.get(ms_name, 0)
        all_runs = [v for v in [r1, r2, r3, r4, r5, r6, r7, r8] if v is not None]
        best = min(all_runs)

        r3_str = f"{r3:.2f}%" if r3 is not None else "N/A"
        best_str = f"{best:.2f}%"
        r8_marker = f"{r8:.2f}%"
        if r8 == best:
            r8_marker = f"*{r8:.2f}%"

        report.append(f"{ms_name:<22} {r1:>6.1f}% {r2:>6.1f}% {r3_str:>7} {r4:>6.2f}% {r5:>6.2f}% {r6:>6.2f}% {r7:>6.2f}% {r8_marker:>7} {best_str:>7}")

    report.append("")
    report.append("* = new best result for this manuscript")
    report.append("")

    # Best results table
    report.append("=" * 80)
    report.append("CURRENT BEST RESULTS (updated with Run 8)")
    report.append("=" * 80)
    report.append("")

    best_data = [
        ('Henslow MS688',      3.80, 'Run 6'),
        ('Sedley MS534',       15.13, 'Run 4'),
        ('Bulkeley MS169',     16.21, 'Run 6'),
        ('Brumwich MS160',      9.30, 'Run 4'),
        ('Jane Jackson MS373', 46.85, 'Run 5'),
    ]

    # Update bests with Run 8 if improved
    for idx, (ms_name, prev_best, prev_run) in enumerate(best_data):
        r8_val = run8_full.get(ms_name, 999)
        if r8_val < prev_best:
            best_data[idx] = (ms_name, r8_val, 'Run 8')

    report.append(f"{'Manuscript':<22} {'Best CER':>10} {'Best Run':>10}")
    report.append("-" * 44)
    for ms_name, best_cer, best_run in best_data:
        report.append(f"{ms_name:<22} {best_cer:>9.2f}% {best_run:>10}")
    report.append("")

    # Run 8 vs previous bests
    report.append("=" * 80)
    report.append("RUN 8 vs PREVIOUS BEST (per manuscript)")
    report.append("=" * 80)
    report.append("")

    prev_bests = {
        'Henslow MS688': (3.80, 'Run 6'),
        'Sedley MS534': (15.13, 'Run 4'),
        'Bulkeley MS169': (16.21, 'Run 6'),
        'Brumwich MS160': (9.30, 'Run 4'),
        'Jane Jackson MS373': (46.85, 'Run 5'),
    }

    for fr in full_results:
        prev_cer, prev_run = prev_bests[fr['name']]
        r8_cer = fr['cer'] * 100
        diff = r8_cer - prev_cer
        if diff < -0.5:
            direction = "BETTER"
        elif diff > 0.5:
            direction = "WORSE"
        else:
            direction = "~SAME"
        report.append(f"  {fr['name']}: {r8_cer:.2f}% vs {prev_cer:.2f}% ({prev_run}) = {direction} ({diff:+.2f}pp)")
    report.append("")

    # Assessment
    report.append("=" * 80)
    report.append("ASSESSMENT")
    report.append("=" * 80)
    report.append("")

    improved = sum(1 for fr in full_results if fr['cer']*100 < prev_bests[fr['name']][0] - 0.5)
    same = sum(1 for fr in full_results if abs(fr['cer']*100 - prev_bests[fr['name']][0]) <= 0.5)
    worse = sum(1 for fr in full_results if fr['cer']*100 > prev_bests[fr['name']][0] + 0.5)

    report.append(f"  Manuscripts improved: {improved}/5")
    report.append(f"  Manuscripts same:     {same}/5")
    report.append(f"  Manuscripts worse:    {worse}/5")
    report.append("")

    for fr, r in zip(full_results, results):
        prev_cer, prev_run = prev_bests[fr['name']]
        r8_full_cer = fr['cer'] * 100
        r8_att_cer = r['cer'] * 100
        coverage = r['ref_length'] / r['full_ref_length'] * 100

        report.append(f"  {fr['name']}:")
        report.append(f"    Full CER: {r8_full_cer:.2f}%  |  Attempted CER: {r8_att_cer:.2f}%  |  Coverage: {coverage:.0f}%")
        report.append(f"    Previous best: {prev_cer:.2f}% ({prev_run})")
        report.append(f"    [...] markers: {r['illegible_markers']}")
        report.append("")

    # Benchmarks
    report.append("=" * 80)
    report.append("BENCHMARK COMPARISON")
    report.append("=" * 80)
    report.append("  < 1% CER  = Very good")
    report.append("  < 5% CER  = Usable for most research purposes")
    report.append("  ~3% CER   = Transkribus Egerton model (best for English secretary hand)")
    report.append("")

    for fr, r in zip(full_results, results):
        cer_pct = fr['cer'] * 100
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
        report.append(f"    Attempted CER: {r['cer']*100:.2f}% (on {coverage:.0f}% of page)")

    report.append(f"\n  Overall Full CER: {overall_full_cer*100:.2f}%")
    report.append(f"  Overall Attempted CER: {overall_attempted_cer*100:.2f}%")
    report.append("")

    report_text = '\n'.join(report)

    output_path = '/Users/sarahbonanno/Desktop/blind-test-run8/run8-evaluation-report.txt'
    with open(output_path, 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()
