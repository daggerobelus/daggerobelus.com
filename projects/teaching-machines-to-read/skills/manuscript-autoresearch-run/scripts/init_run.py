#!/usr/bin/env python3
"""
init_run.py — scaffold one autoresearch run folder and seed its method.md.

The run folder is the mutable workspace the optimizer loop operates on. method.md
is the "train.py analog" the propose agent rewrites each iteration.
"""
import json
import sys
from pathlib import Path

NAIVE_METHOD = "Transcribe this manuscript page. Produce a semi-diplomatic transcription."

_ARMS = {"blind", "faithful"}
_STARTS = {"naive", "best"}

# The best-method seed: the project's cumulative transcription method.
_BEST_SEED = Path(__file__).resolve().parents[2] / "manuscript-transcription" / "SKILL.md"


def init_run(out_root, run_name, arm, start_mode, splits_root, max_iters=40, patience=8) -> str:
    if arm not in _ARMS:
        raise ValueError(f"arm must be one of {_ARMS}, got {arm!r}")
    if start_mode not in _STARTS:
        raise ValueError(f"start_mode must be one of {_STARTS}, got {start_mode!r}")

    run = Path(out_root) / "runs" / run_name
    for sub in ("iterations", "hyp", "final-test-eval", "materials"):
        (run / sub).mkdir(parents=True, exist_ok=True)

    if start_mode == "naive":
        method = NAIVE_METHOD
    else:
        method = _BEST_SEED.read_text(encoding="utf-8")
    (run / "method.md").write_text(method, encoding="utf-8")

    config = {
        "run_name": run_name,
        "arm": arm,
        "start_mode": start_mode,
        "splits_root": str(splits_root),
        "max_iters": max_iters,
        "patience": patience,
    }
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return str(run)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Scaffold one autoresearch run folder.")
    p.add_argument("--out-root", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--arm", required=True, choices=sorted(_ARMS))
    p.add_argument("--start-mode", required=True, choices=sorted(_STARTS))
    p.add_argument("--splits-root", required=True)
    p.add_argument("--max-iters", type=int, default=40)
    p.add_argument("--patience", type=int, default=8)
    a = p.parse_args()
    print(init_run(a.out_root, a.run_name, a.arm, a.start_mode, a.splits_root, a.max_iters, a.patience))
