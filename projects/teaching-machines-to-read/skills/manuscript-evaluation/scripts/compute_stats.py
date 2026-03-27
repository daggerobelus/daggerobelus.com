#!/usr/bin/env python3
"""
compute_stats.py — Statistical Summary for Manuscript Transcription Runs
========================================================================

Takes a list of CER values (one per agent) and computes publication-ready
statistical summaries: mean, median, standard deviation, 95% confidence
interval, interquartile range, and spread.

Uses scipy.stats for confidence intervals to ensure standard methodology.

Usage:
    python compute_stats.py 9.12 10.45 8.87 11.20 9.55 ...
    python compute_stats.py --from-json run-results.json

Output:
    JSON to stdout with all summary statistics.

Dependencies: pip install -r requirements.txt
"""

import argparse
import json
import sys

import numpy as np
from scipy import stats


def _summarize(values):
    """Compute mean, median, std, CI, IQR, spread for a list of numbers."""
    arr = np.array(values, dtype=float)
    n = len(arr)
    if n < 2:
        return {
            "mean": round(float(arr[0]), 2) if n == 1 else None,
            "median": round(float(arr[0]), 2) if n == 1 else None,
            "std_dev": None,
            "ci_95_lower": None,
            "ci_95_upper": None,
            "min": round(float(arr[0]), 2) if n == 1 else None,
            "max": round(float(arr[0]), 2) if n == 1 else None,
            "iqr_lower": None,
            "iqr_upper": None,
            "spread_pp": None,
        }

    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    median = float(np.median(arr))
    q25, q75 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
    se = std / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, df=n - 1)
    ci_lower = mean - t_crit * se
    ci_upper = mean + t_crit * se

    return {
        "mean": round(mean, 2),
        "median": round(median, 2),
        "std_dev": round(std, 2),
        "ci_95_lower": round(ci_lower, 2),
        "ci_95_upper": round(ci_upper, 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
        "iqr_lower": round(q25, 2),
        "iqr_upper": round(q75, 2),
        "spread_pp": round(float(np.max(arr) - np.min(arr)), 2),
    }


def compute_stats(cer_values, coverage_values=None, attempted_cer_values=None):
    """
    Compute publication-ready statistics for a set of CER values.

    Parameters:
        cer_values: list of CER percentages (e.g., [9.12, 10.45, 8.87])
        coverage_values: optional list of coverage fractions (e.g., [0.97, 0.95])
        attempted_cer_values: optional list of attempted CER percentages
            (confident text only, excluding gap-caused deletions)

    Returns:
        dict with statistical summary
    """
    n = len(cer_values)

    result = {
        "num_agents": n,
        "cer": _summarize(cer_values),
    }

    if n < 2:
        result["note"] = "Insufficient data for statistical summary (N < 2)"

    # Attempted CER stats (confident text only)
    if attempted_cer_values is not None and len(attempted_cer_values) > 0:
        result["attempted_cer"] = _summarize(attempted_cer_values)

    # Coverage stats
    if coverage_values is not None and len(coverage_values) > 0:
        cov_arr = np.array(coverage_values, dtype=float)
        result["coverage"] = {
            "mean": round(float(np.mean(cov_arr)), 4),
            "min": round(float(np.min(cov_arr)), 4),
            "max": round(float(np.max(cov_arr)), 4),
        }

    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Compute publication-ready statistics for a set of CER values. '
            'Uses scipy.stats for confidence intervals (t-distribution).'
        ),
        epilog=(
            'Examples:\n'
            '  python compute_stats.py 9.12 10.45 8.87 11.20 9.55\n'
            '  python compute_stats.py --from-json run-14-results.json\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'cer_values',
        nargs='*',
        type=float,
        help='CER values as percentages (e.g., 9.12 10.45 8.87)',
    )
    parser.add_argument(
        '--from-json',
        help='Read CER values from a run results JSON file (agents[].cer field)',
    )
    parser.add_argument(
        '--attempted-cer',
        nargs='*',
        type=float,
        help='Attempted CER values as percentages (confident text only)',
    )

    args = parser.parse_args()

    # Get CER values
    attempted_cer_values = None
    if args.from_json:
        try:
            with open(args.from_json, 'r') as f:
                data = json.load(f)
            cer_values = [agent['cer'] for agent in data['agents']]
            coverage_values = [agent.get('coverage') for agent in data['agents']
                             if agent.get('coverage') is not None]
            attempted_cer_values = [agent.get('attempted_cer') for agent in data['agents']
                                   if agent.get('attempted_cer') is not None]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error reading JSON: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.cer_values:
        cer_values = args.cer_values
        coverage_values = None
        attempted_cer_values = args.attempted_cer if args.attempted_cer else None
    else:
        print("Error: Provide CER values as arguments or use --from-json", file=sys.stderr)
        sys.exit(1)

    if not cer_values:
        print("Error: No CER values provided", file=sys.stderr)
        sys.exit(1)

    result = compute_stats(cer_values, coverage_values, attempted_cer_values)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
