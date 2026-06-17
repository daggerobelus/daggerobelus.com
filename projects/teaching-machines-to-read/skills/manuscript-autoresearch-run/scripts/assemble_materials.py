#!/usr/bin/env python3
"""
assemble_materials.py — build the transcriber's materials folder for one run.

This is the experiment's SINGLE VARIABLE. Both arms get the split's images;
the FAITHFUL (control) arm additionally gets the references in the same folder,
putting the answers within the transcriber's reach. The BLIND (treatment) arm
gets images only.
"""
import json
import shutil
import sys
from pathlib import Path


def assemble(splits_root, split, arm, dest) -> list:
    root = Path(splits_root)
    manifest = json.loads((root / "splits.json").read_text())
    if split not in manifest["splits"]:
        raise ValueError(f"unknown split {split!r}")
    if arm not in ("blind", "faithful"):
        raise ValueError(f"arm must be 'blind' or 'faithful', got {arm!r}")
    pages = manifest["splits"][split]

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    images = root / "corpus" / split / "images"
    refs = root / "corpus" / split / "refs"
    for n in pages:
        shutil.copyfile(images / f"page-{n}.jpg", dest / f"page-{n}.jpg")
        if arm == "faithful":
            shutil.copyfile(refs / f"page-{n}.txt", dest / f"page-{n}.txt")
    return pages


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Assemble per-arm transcriber materials.")
    p.add_argument("--splits-root", required=True)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--arm", required=True, choices=["blind", "faithful"])
    p.add_argument("--dest", required=True)
    a = p.parse_args()
    print(json.dumps(assemble(a.splits_root, a.split, a.arm, a.dest)))
