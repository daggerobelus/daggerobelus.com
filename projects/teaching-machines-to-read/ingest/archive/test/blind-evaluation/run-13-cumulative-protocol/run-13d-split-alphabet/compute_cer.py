#!/usr/bin/env python3
"""
Compute Character Error Rate (CER) for Run 13d blind transcription evaluation.
Generation effect + cumulative error protocol → Brumwich MS160.

5 independent agents, each studying 5 Henslow training pairs, writing their own
guide (generation effect), reading the cumulative error protocol, then transcribing
Brumwich MS160 page 10.
"""

import re
import os


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


def normalize_blind(text):
    """Normalize a blind transcription for CER comparison."""
    content = text

    # Remove header/metadata lines before the actual transcription starts.
    # The transcription always begins with a recipe title starting with "A "
    # or a page marker like [Left page]. Strip everything before that.
    lines = content.split('\n')
    clean_lines = []
    found_start = False
    for line in lines:
        stripped = line.strip()
        # Skip blank lines before content starts
        if not found_start and not stripped:
            continue
        # Skip header/separator/metadata lines
        if not found_start:
            if '=====' in stripped or '------' in stripped:
                continue
            if any(kw in stripped.lower() for kw in [
                'transcription', 'brumwich', 'agent ', 'run 13',
                'note:', 'self-taught', 'cumulative', 'protocol',
                'alphabet', 'full stack', 'marks genuinely',
                'this image shows', 'i transcribe'
            ]):
                continue
            # Content starts with recipe text or page markers
            found_start = True
        clean_lines.append(line)
    content = '\n'.join(clean_lines)

    # Strip page labels
    content = re.sub(r'\[Left page[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Right page[^\]]*\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[Page[^\]]*\]', '', content, flags=re.IGNORECASE)

    # Replace [...] with space (illegible markers)
    content = re.sub(r'\[\.\.\.\]', ' ', content)

    # Strip decorative dot patterns
    content = re.sub(r'\.{3,}', '', content)

    # Handle [word?] -> word (confidence markers)
    content = re.sub(r'\[([^\]]*?)\?\]', r'\1', content)

    # Strip remaining editorial brackets
    content = re.sub(r'\[([^\]]*?)\]', r'\1', content)

    # Collapse whitespace
    content = re.sub(r'\s+', ' ', content)
    return content.strip()


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
    # Handle [...] in reference
    content = re.sub(r'\[\.+\]', '', content)
    # Strip editorial brackets
    content = re.sub(r'\[([^\]]*?)\]', r'\1', content)
    # Strip superscript ^
    content = re.sub(r'\^', '', content)
    # Collapse whitespace
    content = re.sub(r'\s+', ' ', content)
    return content.strip()


def main():
    base = os.path.expanduser('~/Desktop/run-13d-split-alphabet')
    ref_path = os.path.join(base, 'evaluation', 'brumwich-reference.txt')

    with open(ref_path, 'r') as f:
        ref_raw = f.read()
    ref_text = normalize_reference(ref_raw)

    report = []
    report.append("=" * 80)
    report.append("BLIND TRANSCRIPTION EVALUATION REPORT — RUN 13d")
    report.append("Generation Effect + Cumulative Error Protocol + Split Alphabet → Brumwich MS160")
    report.append("Date: 2026-03-27")
    report.append("=" * 80)
    report.append("")
    report.append("METHOD")
    report.append("-" * 80)
    report.append("Each of 5 independent agents:")
    report.append("  1. Studied 5 Henslow MS688 training pairs (image + transcription)")
    report.append("  2. Wrote their own self-taught guide (generation effect)")
    report.append("  3. Read the cumulative error protocol (Henslow + Sedley errors)")
    report.append("  4. Transcribed Brumwich MS160 page 10 (unseen manuscript)")
    report.append("")
    report.append("This combines the generation effect (Run 11) with the cumulative")
    report.append("error protocol (Run 13), plus the alphabet-first method (Run 4). Compare to Run 4 baseline (9.30% CER,")
    report.append("alphabet-first only, no generation effect or error protocol).")
    report.append("")
    report.append("CER = (Substitutions + Insertions + Deletions) / Total Reference Characters")
    report.append("")

    report.append("=" * 80)
    report.append("INDIVIDUAL AGENT RESULTS — Brumwich MS160")
    report.append("=" * 80)

    agent_cers = []
    ref_len = len(ref_text)

    for agent_num in range(1, 6):
        blind_path = os.path.join(base, f'agent-{agent_num}b', 'output',
                                   'brumwich-ms160-transcription.txt')
        with open(blind_path, 'r') as f:
            blind_raw = f.read()

        blind_text = normalize_blind(blind_raw)
        dist, subs, ins, dels = levenshtein_distance(blind_text, ref_text)
        cer = dist / ref_len if ref_len > 0 else 0
        agent_cers.append(cer * 100)

        report.append("")
        report.append(f"--- Agent {agent_num} ---")
        report.append(f"  Reference length:  {ref_len} characters")
        report.append(f"  Blind length:      {len(blind_text)} characters")
        report.append(f"  Edit distance:     {dist}")
        report.append(f"    Substitutions:   {subs}")
        report.append(f"    Insertions:      {ins}")
        report.append(f"    Deletions:       {dels}")
        report.append(f"  CER:               {cer*100:.2f}%")
        report.append("")
        report.append(f"  Blind text (first 200 chars):")
        report.append(f"    {blind_text[:200]}")
        report.append(f"  Reference text (first 200 chars):")
        report.append(f"    {ref_text[:200]}")

    # Summary
    avg_cer = sum(agent_cers) / len(agent_cers)
    best_cer = min(agent_cers)
    worst_cer = max(agent_cers)
    spread = worst_cer - best_cer
    best_agent = agent_cers.index(best_cer) + 1

    report.append("")
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    report.append("")
    report.append(f"  {'Agent':<10} {'CER':>8}")
    report.append(f"  {'-'*10} {'-'*8}")
    for i, cer in enumerate(agent_cers):
        marker = " <-- best" if cer == best_cer else ""
        report.append(f"  Agent {i+1:<4} {cer:>7.2f}%{marker}")
    report.append("")
    report.append(f"  Average CER:   {avg_cer:.2f}%")
    report.append(f"  Best CER:      {best_cer:.2f}% (Agent {best_agent})")
    report.append(f"  Worst CER:     {worst_cer:.2f}%")
    report.append(f"  Spread:        {spread:.2f} percentage points")
    report.append("")

    # Comparison to previous runs
    report.append("=" * 80)
    report.append("COMPARISON — Brumwich MS160 across runs")
    report.append("=" * 80)
    report.append("")
    report.append(f"  {'Run':<40} {'CER':>8}")
    report.append(f"  {'-'*40} {'-'*8}")
    comparisons = [
        ("Run 1 (basic blind)", 96.10),
        ("Run 2 (updated guide)", 93.00),
        ("Run 4 (alphabet-first)", 9.30),
        ("Run 5 (stronger instructions)", 50.62),
        ("Run 6 (alphabet + vocab)", 69.29),
        ("Run 7 (visual reference)", 62.49),
        (f"Run 13d avg (generation + protocol)", avg_cer),
        (f"Run 13d best (Agent {best_agent})", best_cer),
    ]
    for name, cer in comparisons:
        marker = ""
        if "13d" in name:
            marker = " ***"
        report.append(f"  {name:<40} {cer:>7.2f}%{marker}")
    report.append("")
    report.append(f"  Previous best: 9.30% (Run 4, alphabet-first)")
    diff = avg_cer - 9.30
    if diff < 0:
        report.append(f"  Run 13d avg vs previous best: {diff:+.2f}pp (IMPROVED)")
    else:
        report.append(f"  Run 13d avg vs previous best: {diff:+.2f}pp")
    diff_best = best_cer - 9.30
    if diff_best < 0:
        report.append(f"  Run 13d best vs previous best: {diff_best:+.2f}pp (IMPROVED)")
    else:
        report.append(f"  Run 13d best vs previous best: {diff_best:+.2f}pp")
    report.append("")

    # Benchmarks
    report.append("=" * 80)
    report.append("BENCHMARK")
    report.append("=" * 80)
    report.append("  < 1% CER  = Very good")
    report.append("  < 5% CER  = Usable for most research purposes")
    report.append("  ~3% CER   = Transkribus Egerton model (best for English secretary hand)")
    report.append("  < 10% CER = Moderate (needs review)")
    report.append("  <20% CER  = Poor (heavy editing needed)")
    report.append("  20%+ CER  = Not usable")
    report.append("")

    for i, cer in enumerate(agent_cers):
        if cer < 1:
            quality = "VERY GOOD"
        elif cer < 5:
            quality = "USABLE"
        elif cer < 10:
            quality = "MODERATE"
        elif cer < 20:
            quality = "POOR"
        else:
            quality = "NOT USABLE"
        report.append(f"  Agent {i+1}: {cer:.2f}% — {quality}")
    report.append(f"  Average: {avg_cer:.2f}%")
    report.append("")

    report_text = '\n'.join(report)

    # Save report
    output_path = os.path.join(base, 'evaluation', 'run-13d-evaluation-report.txt')
    with open(output_path, 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()
