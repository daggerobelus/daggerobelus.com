#!/usr/bin/env python3
"""
ledger.py — the ratchet record for an autoresearch run.

results.tsv is the append-only log (one row per iteration). Each KEPT
iteration also snapshots method.md into iterations/iter-NN/ so the winning
method at every step is recoverable — the "git ratchet" as plain folders.
"""
import shutil
from pathlib import Path

RESULTS_HEADER = ["iter", "change_description", "val_diplomatic_cer",
                  "val_reading_cer", "kept", "snapshot_path"]


def _results_path(run_dir: str) -> Path:
    return Path(run_dir) / "results.tsv"


def append_result(run_dir, iter_n, change_description, dipl_cer, read_cer, kept, snapshot_path) -> None:
    path = _results_path(run_dir)
    new = not path.exists()
    # tabs/newlines would corrupt the TSV; collapse them in free text.
    desc = " ".join(str(change_description).split())
    snap = " ".join(str(snapshot_path).split())
    row = [str(iter_n), desc, f"{dipl_cer:.6f}", f"{read_cer:.6f}",
           "1" if kept else "0", snap]
    with path.open("a", encoding="utf-8") as f:
        if new:
            f.write("\t".join(RESULTS_HEADER) + "\n")
        f.write("\t".join(row) + "\n")


def read_results(run_dir) -> list:
    path = _results_path(run_dir)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines[1:]:  # skip header
        if not line.strip():
            continue
        cells = line.split("\t")
        rows.append({
            "iter": int(cells[0]),
            "change_description": cells[1],
            "val_diplomatic_cer": float(cells[2]),
            "val_reading_cer": float(cells[3]),
            "kept": cells[4] == "1",
            "snapshot_path": cells[5] if len(cells) > 5 else "",
        })
    return rows


def best_so_far(run_dir):
    kept = [r for r in read_results(run_dir) if r["kept"]]
    if not kept:
        return None
    best = min(kept, key=lambda r: r["val_diplomatic_cer"])
    return (best["val_diplomatic_cer"], best["iter"])


def best_method_path(run_dir):
    kept = [r for r in read_results(run_dir) if r["kept"]]
    if not kept:
        return None
    best = min(kept, key=lambda r: r["val_diplomatic_cer"])
    return best["snapshot_path"]


def snapshot_method(run_dir, iter_n, method_path) -> str:
    dst_dir = Path(run_dir) / "iterations" / f"iter-{int(iter_n):02d}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "method.md"
    shutil.copyfile(method_path, dst)
    return str(dst)
