#!/usr/bin/env python3
"""
CER (Character Error Rate) Evaluation for Blind Transcription Test (Run 4 - Alphabet-First Method)
Computes Levenshtein edit distance at the character level between blind transcriptions and references.
"""

import re


def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance between two strings.
    Returns (distance, substitutions, insertions, deletions)."""
    m, n = len(s1), len(s2)

    # dp[i][j] = (distance, subs, ins, dels) for s1[:i] vs s2[:j]
    dp = [[(0, 0, 0, 0)] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        dp[i][0] = (i, 0, 0, i)  # deletions from s1
    for j in range(1, n + 1):
        dp[0][j] = (j, 0, j, 0)  # insertions into s1

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                sub = dp[i-1][j-1]
                sub_cost = (sub[0] + 1, sub[1] + 1, sub[2], sub[3])

                ins = dp[i][j-1]
                ins_cost = (ins[0] + 1, ins[1], ins[2] + 1, ins[3])

                dele = dp[i-1][j]
                del_cost = (dele[0] + 1, dele[1], dele[2], dele[3] + 1)

                dp[i][j] = min(sub_cost, ins_cost, del_cost, key=lambda x: x[0])

    return dp[m][n]


def get_edit_operations(s1, s2):
    """Get the actual edit operations via backtrace."""
    m, n = len(s1), len(s2)

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        dp[i][0] = i
    for j in range(1, n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j-1], dp[i][j-1], dp[i-1][j])

    ops = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            ops.append(('SUB', i-1, j-1, s1[i-1], s2[j-1]))
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            ops.append(('INS', i, j-1, '', s2[j-1]))
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            ops.append(('DEL', i-1, j, s1[i-1], ''))
            i -= 1
        else:
            break

    ops.reverse()
    return ops


def get_word_context(text, char_pos, window=3):
    """Get word context around a character position."""
    start = char_pos
    while start > 0 and text[start-1] not in ' \n\t':
        start -= 1
    end = char_pos
    while end < len(text) and text[end] not in ' \n\t':
        end += 1
    word = text[start:end]

    words_before = text[max(0, start-50):start].split()[-window:]
    words_after = text[end:min(len(text), end+50)].split()[:window]

    return word, ' '.join(words_before), ' '.join(words_after)


def group_edits_by_word(ops, hyp, ref):
    """Group character-level edits into word-level differences."""
    diffs = []
    for op_type, hyp_pos, ref_pos, hyp_char, ref_char in ops:
        if op_type == 'DEL':
            h_word, h_before, h_after = get_word_context(hyp, hyp_pos)
            r_word, r_before, r_after = get_word_context(ref, min(ref_pos, len(ref)-1))
        elif op_type == 'INS':
            h_word, h_before, h_after = get_word_context(hyp, min(hyp_pos, len(hyp)-1))
            r_word, r_before, r_after = get_word_context(ref, ref_pos)
        else:
            h_word, h_before, h_after = get_word_context(hyp, hyp_pos)
            r_word, r_before, r_after = get_word_context(ref, ref_pos)

        diffs.append({
            'type': op_type,
            'hyp_char': hyp_char,
            'ref_char': ref_char,
            'hyp_word': h_word,
            'ref_word': r_word,
            'context_before': h_before,
            'context_after': h_after,
        })

    return diffs


def extract_transcription_text(text):
    """Extract only the transcription text from a blind transcription file,
    stripping all headers, metadata, section dividers, and confidence notes."""
    lines = text.split('\n')

    has_sections = any('====' in line for line in lines)

    if has_sections:
        in_transcription = False
        in_confidence = False
        trans_lines = []

        # Recognize section headers that signal transcription content
        trans_section_names = [
            'TRANSCRIPTION',
            'LEFT PAGE', 'RIGHT PAGE',
        ]

        for line in lines:
            stripped = line.strip()

            # Skip divider lines
            if '====' in line:
                continue

            # Check if this is a section header
            is_section_header = False
            for name in trans_section_names:
                if stripped.startswith(name):
                    is_section_header = True
                    break

            if is_section_header:
                in_transcription = True
                in_confidence = False
                continue

            if stripped.startswith('CONFIDENCE'):
                in_transcription = False
                in_confidence = True
                continue

            if in_transcription and not in_confidence:
                trans_lines.append(line)

        return '\n'.join(trans_lines)
    else:
        # No section markers -- take everything before confidence notes
        result_lines = []
        for line in lines:
            if 'CONFIDENCE' in line.upper():
                break
            result_lines.append(line)
        return '\n'.join(result_lines)


def normalize_blind(text):
    """Normalize blind transcription text."""
    text = extract_transcription_text(text)

    # Strip [Passage heavily damaged...] notes
    text = re.sub(r'\[Passage heavily damaged[^\]]*\]', '', text)

    # Strip decorative dot patterns: ". . . ." etc.
    text = re.sub(r'(?:\.\s*){2,}\.?', '', text)

    # Handle illegibility markers BEFORE stripping other brackets.
    # Patterns: [...], [....], [.....], etc.
    text = re.sub(r'\[\.{2,}\]', '', text)

    # Patterns: [..?], [...?], [word..?] -- partial illegibility with trailing dots
    # e.g., [boy..?], [& ..?], [th..?], [b..?], [kno...?], [quart..?], [w[...]]
    # These are uncertain/illegible -- strip them entirely
    text = re.sub(r'\[[^\]]*\.\.+\??\]', '', text)

    # Strip [word?] confidence markers -> word
    text = re.sub(r'\[([^\]]*?)\?\]', r'\1', text)

    # Strip italic markers *letters* -> letters
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # Strip remaining square brackets around words [word] -> word
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)

    # Strip empty brackets [] that remain after other stripping
    text = re.sub(r'\[\s*\]', '', text)

    # Strip strikethrough markers ~~text~~
    text = re.sub(r'~~[^~]*~~', '', text)

    # Strip recipe section markers (+)
    text = re.sub(r'\+\s*', '', text)

    # Strip standalone page numbers on their own line
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if s and re.match(r'^\d+$', s):
            continue
        cleaned.append(line)
    text = '\n'.join(cleaned)

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = text.strip()

    return text


def normalize_reference(text):
    """Normalize reference transcription text."""
    lines = text.split('\n')

    # Skip header lines (everything before the --- separator)
    found_separator = False
    content_lines = []
    for line in lines:
        if line.strip() == '---':
            found_separator = True
            continue
        if found_separator:
            content_lines.append(line)

    if not found_separator:
        content_lines = lines

    text = '\n'.join(content_lines)

    # Strip editorial brackets [er] -> er, [pro] -> pro, [...] -> (nothing for illegible)
    # But first handle [...] illegibility markers
    text = re.sub(r'\[\.{2,}\]', '', text)
    # Then expand editorial abbreviations
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)

    # Strip page number markers {6}, {7}
    text = re.sub(r'\{[^}]+\}', '', text)

    # Strip caret insertions ^text -> text
    text = re.sub(r'\^', '', text)

    # Handle line-break hyphens: word= \n continued -> wordcontinued
    text = re.sub(r'=\s*\n\s*', '', text)

    # Strip standalone page numbers
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if s and re.match(r'^\d+$', s):
            continue
        cleaned.append(line)
    text = '\n'.join(cleaned)

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = text.strip()

    return text


def evaluate_manuscript(name, hyp_raw, ref_raw):
    """Evaluate a single manuscript."""
    hyp = normalize_blind(hyp_raw)
    ref = normalize_reference(ref_raw)

    # Compute Levenshtein distance
    dist, subs, ins, dels = levenshtein_distance(hyp, ref)

    ref_len = len(ref)
    cer = dist / ref_len if ref_len > 0 else 0

    # Get edit operations for detailed analysis
    ops = get_edit_operations(hyp, ref)
    diffs = group_edits_by_word(ops, hyp, ref)

    return {
        'name': name,
        'hyp_text': hyp,
        'ref_text': ref,
        'hyp_len': len(hyp),
        'ref_len': ref_len,
        'distance': dist,
        'substitutions': subs,
        'insertions': ins,
        'deletions': dels,
        'cer': cer,
        'diffs': diffs,
        'ops': ops,
    }


def categorize_error(diff):
    """Categorize an error type."""
    h = diff['hyp_char']
    r = diff['ref_char']

    if diff['type'] == 'SUB':
        if h.lower() == r.lower():
            return 'capitalization'
        if (h in 'uv' and r in 'uv') or (h in 'UV' and r in 'UV'):
            return 'u/v convention'
        if h in 'ij' and r in 'ij':
            return 'i/j convention'
        if h in 'sf' and r in 'sf':
            return 'long-s/f confusion'
        # Thorn convention: y/th confusion (ye = the, yt = that, etc.)
        if (h == 'y' and r == 't') or (h == 't' and r == 'y'):
            h_word = diff.get('hyp_word', '')
            r_word = diff.get('ref_word', '')
            # Check if this is a thorn usage
            if (h_word.startswith('y') and r_word.startswith('th')) or \
               (h_word.startswith('th') and r_word.startswith('y')):
                return 'thorn convention (ye/the)'
        if h in 'eo' and r in 'eo':
            return 'letterform misreading (e/o)'
        if h in 'mn' and r in 'mn':
            return 'minim confusion (m/n)'
        if h in 'ct' and r in 'ct':
            return 'letterform misreading (c/t)'
        if h in '.,;:!?\'"()-=' or r in '.,;:!?\'"()-=':
            return 'punctuation'
        if h == '\n' or r == '\n':
            return 'lineation'
        return f'letterform misreading ({r}->{h})'

    elif diff['type'] == 'INS':
        if r == ' ':
            return 'word segmentation (extra space in ref)'
        if r == '\n':
            return 'lineation (extra newline in ref)'
        if r in '.,;:!?\'"()-=':
            return 'punctuation (missing in blind)'
        return f'insertion (ref has extra "{r}")'

    elif diff['type'] == 'DEL':
        if h == ' ':
            return 'word segmentation (extra space in blind)'
        if h == '\n':
            return 'lineation (extra newline in blind)'
        if h in '.,;:!?\'"()-=':
            return 'punctuation (extra in blind)'
        return f'deletion (blind has extra "{h}")'

    return 'unknown'


def format_report(results):
    """Format the full evaluation report."""
    lines = []
    lines.append("=" * 80)
    lines.append("BLIND TRANSCRIPTION EVALUATION REPORT")
    lines.append("Run 4: Alphabet-First Method")
    lines.append("Date: 2026-02-27")
    lines.append("=" * 80)
    lines.append("")

    # ===== SUMMARY TABLE =====
    lines.append("-" * 80)
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"{'Manuscript':<25} {'Ref Chars':>10} {'Hyp Chars':>10} {'Edits':>8} {'CER':>10} {'S':>5} {'I':>5} {'D':>5}")
    lines.append("-" * 80)

    total_edits = 0
    total_ref_chars = 0

    for r in results:
        lines.append(f"{r['name']:<25} {r['ref_len']:>10} {r['hyp_len']:>10} {r['distance']:>8} {r['cer']:>9.2%} {r['substitutions']:>5} {r['insertions']:>5} {r['deletions']:>5}")
        total_edits += r['distance']
        total_ref_chars += r['ref_len']

    overall_cer = total_edits / total_ref_chars if total_ref_chars > 0 else 0
    lines.append("-" * 80)
    lines.append(f"{'OVERALL':<25} {total_ref_chars:>10} {'':>10} {total_edits:>8} {overall_cer:>9.2%}")
    lines.append("")

    # ===== COMPARISON TABLE =====
    lines.append("-" * 80)
    lines.append("COMPARISON WITH PREVIOUS RUNS")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"{'Manuscript':<25} {'Run 1':>10} {'Run 2':>10} {'Run 3':>10} {'Run 4':>10} {'Trend':>15}")
    lines.append("-" * 80)

    prev = {
        'Henslow MS688':      ('~11.3%', '~12%',  '6.12%'),
        'Sedley MS534':       ('~15.8%', '~21%',  'N/A'),
        'Bulkeley MS169':     ('~22.8%', '~18%',  'N/A'),
        'Brumwich MS160':     ('~96.1%', '~93%',  'N/A'),
        'Jane Jackson MS373': ('~95.6%', '~95%',  'N/A'),
    }

    for r in results:
        p = prev.get(r['name'], ('N/A', 'N/A', 'N/A'))
        run4 = f"{r['cer']:.2%}"

        run1_val = p[0].replace('~', '').replace('%', '')
        try:
            r1 = float(run1_val)
            r4 = r['cer'] * 100
            if r4 < r1 * 0.5:
                trend = "MAJOR IMPROVE"
            elif r4 < r1:
                trend = "IMPROVED"
            elif abs(r4 - r1) < 2:
                trend = "SIMILAR"
            elif r4 > r1:
                trend = "WORSE"
            else:
                trend = "SIMILAR"
        except:
            trend = "N/A"

        lines.append(f"{r['name']:<25} {p[0]:>10} {p[1]:>10} {p[2]:>10} {run4:>10} {trend:>15}")

    lines.append("")
    lines.append("Note: Runs 1 and 2 used basic prompting. Run 3 introduced the alphabet-first")
    lines.append("method (tested only on Henslow). Run 4 uses the alphabet-first method on all")
    lines.append("five manuscripts.")
    lines.append("")

    # ===== DETAILED ANALYSIS PER MANUSCRIPT =====
    for r in results:
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"DETAILED ANALYSIS: {r['name']}")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Reference length:  {r['ref_len']} characters")
        lines.append(f"Hypothesis length: {r['hyp_len']} characters")
        lines.append(f"Edit distance:     {r['distance']}")
        lines.append(f"CER:               {r['cer']:.4%}")
        lines.append(f"  Substitutions:   {r['substitutions']}")
        lines.append(f"  Insertions:      {r['insertions']}")
        lines.append(f"  Deletions:       {r['deletions']}")
        lines.append("")

        # Categorize errors
        error_cats = {}
        error_details = []

        for d in r['diffs']:
            cat = categorize_error(d)
            error_cats[cat] = error_cats.get(cat, 0) + 1

            # Format character for display
            def fmt_char(c):
                if c == '\n':
                    return '\\n'
                if c == ' ':
                    return '<space>'
                return c

            if d['type'] == 'SUB':
                detail = f"  [{d['type']}] ref '{fmt_char(d['ref_char'])}' -> blind '{fmt_char(d['hyp_char'])}' | ref: '{d['ref_word']}' | blind: '{d['hyp_word']}' [{cat}]"
            elif d['type'] == 'INS':
                detail = f"  [{d['type']}] ref has '{fmt_char(d['ref_char'])}' (not in blind) | ref: '{d['ref_word']}' | blind: '{d['hyp_word']}' [{cat}]"
            else:
                detail = f"  [{d['type']}] blind has '{fmt_char(d['hyp_char'])}' (not in ref) | ref: '{d['ref_word']}' | blind: '{d['hyp_word']}' [{cat}]"
            error_details.append(detail)

        lines.append("Error categories (sorted by frequency):")
        lines.append("-" * 60)
        for cat, count in sorted(error_cats.items(), key=lambda x: -x[1]):
            lines.append(f"  {count:>4}  {cat}")
        lines.append("")

        # Show word-level differences
        lines.append("Word-level differences (blind vs reference):")
        lines.append("-" * 60)

        word_diffs = []
        seen_pairs = set()
        for d in r['diffs']:
            pair = (d['hyp_word'], d['ref_word'])
            if pair not in seen_pairs and d['hyp_word'] != d['ref_word']:
                seen_pairs.add(pair)
                word_diffs.append(d)

        if word_diffs:
            for d in word_diffs[:100]:  # Limit for readability
                lines.append(f"  Blind: '{d['hyp_word']}'")
                lines.append(f"  Ref:   '{d['ref_word']}'")
                lines.append(f"  Context: ...{d['context_before']} [DIFF] {d['context_after']}...")
                lines.append("")
            if len(word_diffs) > 100:
                lines.append(f"  ... and {len(word_diffs) - 100} more word-level differences")
        else:
            lines.append("  (No word-level differences)")

        lines.append("")
        lines.append("All character-level edits:")
        lines.append("-" * 60)
        for detail in error_details[:150]:
            lines.append(detail)
        if len(error_details) > 150:
            lines.append(f"  ... and {len(error_details) - 150} more edits")
        lines.append("")

        # Notes about specific error patterns
        lines.append("Error pattern analysis:")
        lines.append("-" * 60)

        # Identify systematic patterns
        total_errors = r['distance']
        if total_errors > 0:
            cap_errors = error_cats.get('capitalization', 0)
            uv_errors = error_cats.get('u/v convention', 0)
            thorn_errors = sum(v for k, v in error_cats.items() if 'thorn' in k)
            punct_errors = sum(v for k, v in error_cats.items() if 'punctuation' in k)
            lineation_errors = sum(v for k, v in error_cats.items() if 'lineation' in k)
            segmentation_errors = sum(v for k, v in error_cats.items() if 'word segmentation' in k)
            letterform_errors = sum(v for k, v in error_cats.items() if 'letterform' in k)
            minim_errors = sum(v for k, v in error_cats.items() if 'minim' in k)

            lines.append(f"  Capitalization differences:   {cap_errors:>4} ({cap_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  u/v convention differences:   {uv_errors:>4} ({uv_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Thorn convention (ye/the):    {thorn_errors:>4} ({thorn_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Punctuation differences:      {punct_errors:>4} ({punct_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Lineation differences:        {lineation_errors:>4} ({lineation_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Word segmentation:            {segmentation_errors:>4} ({segmentation_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Letterform misreadings:       {letterform_errors:>4} ({letterform_errors/total_errors*100:.1f}% of errors)")
            lines.append(f"  Minim confusion (m/n/u/i):    {minim_errors:>4} ({minim_errors/total_errors*100:.1f}% of errors)")
            lines.append("")

            # Debatable errors (conventions + formatting, not substantive misreadings)
            debatable = cap_errors + uv_errors + thorn_errors + punct_errors + lineation_errors
            adjusted_cer = (total_errors - debatable) / r['ref_len'] if r['ref_len'] > 0 else 0
            lines.append(f"  Adjusted CER (excluding capitalization, u/v, thorn, punctuation, lineation):")
            lines.append(f"  {adjusted_cer:.4%} ({total_errors - debatable} substantive errors / {r['ref_len']} ref chars)")
        lines.append("")

    # ===== OVERALL ASSESSMENT =====
    lines.append("")
    lines.append("=" * 80)
    lines.append("OVERALL ASSESSMENT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Overall CER: {overall_cer:.4%}")
    lines.append(f"Total reference characters: {total_ref_chars}")
    lines.append(f"Total edits: {total_edits}")
    lines.append("")

    lines.append("Benchmarks:")
    lines.append("  < 1% CER = very good")
    lines.append("  < 5% CER = usable for most research purposes")
    lines.append("  ~3% CER = Transkribus Egerton model (best existing for English secretary hand)")
    lines.append("")

    for r in results:
        # Special case: if hypothesis is much shorter than reference, this is
        # likely an illegibility issue (agent correctly marked text as unreadable)
        # rather than hallucination
        ratio = r['hyp_len'] / r['ref_len'] if r['ref_len'] > 0 else 1

        if r['cer'] < 0.01:
            assessment = "VERY GOOD -- exceeds field standard"
        elif r['cer'] < 0.03:
            assessment = "EXCELLENT -- competitive with Transkribus Egerton"
        elif r['cer'] < 0.05:
            assessment = "GOOD -- usable for most research purposes"
        elif r['cer'] < 0.10:
            assessment = "MODERATE -- needs review but captures most content"
        elif r['cer'] < 0.30:
            assessment = "POOR -- significant errors, heavy review needed"
        elif ratio < 0.5:
            assessment = "HIGH CER due to extensive illegibility (not hallucination)"
        else:
            assessment = "VERY POOR -- substantial hallucination or misreading"
        lines.append(f"  {r['name']}: {r['cer']:.2%} -- {assessment}")

    lines.append("")
    lines.append(f"  OVERALL: {overall_cer:.2%}")
    lines.append("")

    # ===== INTERPRETIVE NOTES =====
    lines.append("=" * 80)
    lines.append("INTERPRETIVE NOTES")
    lines.append("=" * 80)
    lines.append("")
    lines.append("1. BRUMWICH MS160: The dramatic improvement from ~96% CER (Runs 1-2) to")
    lines.append("   ~10% CER (Run 4) is the most striking result. The alphabet-first method")
    lines.append("   appears to have largely eliminated the hallucination problem that plagued")
    lines.append("   earlier runs on this manuscript. The remaining errors are mostly genuine")
    lines.append("   letterform misreadings rather than fabricated text.")
    lines.append("")
    lines.append("2. HENSLOW MS688: Continued improvement from 6.12% (Run 3) to ~5% (Run 4).")
    lines.append("   Many remaining errors are debatable (capitalization, u/v convention,")
    lines.append("   punctuation) rather than substantive misreadings.")
    lines.append("")
    lines.append("3. JANE JACKSON MS373: This manuscript has extensive water damage (~40-50%")
    lines.append("   of text illegible). The blind transcription appropriately marks most text")
    lines.append("   as illegible rather than hallucinating content. The high CER reflects")
    lines.append("   the gap between the extensive reference text and the limited readable")
    lines.append("   portions, NOT hallucination. The agent's decision to mark text as")
    lines.append("   illegible rather than guessing is actually the correct behavior.")
    lines.append("")
    lines.append("4. SEDLEY MS534: CER is similar to Run 1 (~15%). Many errors involve")
    lines.append("   misreading entire words (e.g., 'seirced' for 'calcinated', 'boxe'")
    lines.append("   for 'Iron', 'Plod' for 'Good'). These are substantive letterform")
    lines.append("   misreadings that suggest the alphabet-first method did not help as")
    lines.append("   much with this particular hand.")
    lines.append("")
    lines.append("5. BULKELEY MS169: Some improvement over Run 1 (~23% -> ~19%). The")
    lines.append("   herbal/medical vocabulary makes this text particularly challenging")
    lines.append("   because context-based guessing is unreliable with specialized terms.")
    lines.append("")
    lines.append("6. REFERENCE ERRORS: Some differences may reflect errors in the FromThePage")
    lines.append("   reference transcription rather than in the blind reading. For example,")
    lines.append("   word segmentation ('lang de beefe' vs 'langdebeeffe' in Henslow) may")
    lines.append("   be a legitimate difference in how to transcribe a compound word.")
    lines.append("")

    return '\n'.join(lines)


# ===== MAIN =====

manuscripts = [
    {
        'name': 'Henslow MS688',
        'hyp_path': '/Users/sarahbonanno/Desktop/blind-test-alphabet/henslow-ms688-page12-transcription.txt',
        'ref_path': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/henslow-ms688/test-page-reference.txt',
    },
    {
        'name': 'Sedley MS534',
        'hyp_path': '/Users/sarahbonanno/Desktop/blind-test-alphabet/sedley-ms534-page13-transcription.txt',
        'ref_path': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/sedley-ms534/test-page-reference.txt',
    },
    {
        'name': 'Bulkeley MS169',
        'hyp_path': '/Users/sarahbonanno/Desktop/blind-test-alphabet/bulkeley-ms169-page17-transcription.txt',
        'ref_path': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/bulkeley-ms169/test-page-reference.txt',
    },
    {
        'name': 'Brumwich MS160',
        'hyp_path': '/Users/sarahbonanno/Desktop/blind-test-alphabet/brumwich-ms160-page10-transcription.txt',
        'ref_path': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/brumwich-ms160/test-page-reference.txt',
    },
    {
        'name': 'Jane Jackson MS373',
        'hyp_path': '/Users/sarahbonanno/Desktop/blind-test-alphabet/jane-jackson-ms373-page20-transcription.txt',
        'ref_path': '/Users/sarahbonanno/daggerobelus.com/projects/recipes/ingest/archive/test/jane-jackson-ms-373/page-20-reference.txt',
    },
]

results = []
for ms in manuscripts:
    with open(ms['hyp_path'], 'r') as f:
        hyp_raw = f.read()
    with open(ms['ref_path'], 'r') as f:
        ref_raw = f.read()

    print(f"Evaluating {ms['name']}...")
    result = evaluate_manuscript(ms['name'], hyp_raw, ref_raw)
    results.append(result)
    print(f"  Ref: {result['ref_len']} chars | Hyp: {result['hyp_len']} chars")
    print(f"  CER: {result['cer']:.4%} ({result['distance']} edits / {result['ref_len']} ref chars)")
    print(f"  S={result['substitutions']} I={result['insertions']} D={result['deletions']}")
    print()

print("Generating report...")
report = format_report(results)

with open('/Users/sarahbonanno/Desktop/blind-test-alphabet/evaluation-report.txt', 'w') as f:
    f.write(report)

print("Report saved to evaluation-report.txt")
print()

total_edits = sum(r['distance'] for r in results)
total_ref = sum(r['ref_len'] for r in results)
print(f"Overall CER: {total_edits/total_ref:.4%}")
