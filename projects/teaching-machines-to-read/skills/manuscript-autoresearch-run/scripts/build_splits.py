#!/usr/bin/env python3
"""
build_splits.py — freeze the Sedley dev/val/test split and copy it into an
isolated layout for the autoresearch experiment.

Isolation is deliberate: val/test images and references live in SEPARATE
folders so a transcriber subagent can be handed images with no path to the
answers. dev keeps image+ref together because dev is the study pool.

Usage:
    python build_splits.py SOURCE_DIR OUT_ROOT
    # SOURCE_DIR e.g. ingest/archive/sedley-ms534-full
    # OUT_ROOT   e.g. ingest/archive/test/autoresearch-sedley-01
"""
import json
import shutil
import sys
from pathlib import Path

# Frozen split — DO NOT regenerate randomly. Same for all four runs.
SPLITS = {
    "dev":  ["003", "006", "009", "012", "015", "018", "021", "024", "027", "030", "033", "036", "039"],
    "val":  ["004", "007", "010", "013", "016", "019", "022", "025", "028", "031", "034", "037", "041"],
    "test": ["005", "008", "011", "014", "017", "020", "023", "026", "029", "032", "035", "038", "042"],
}

MANUSCRIPT = "sedley-ms534"


def _src_img(src: Path, n: str) -> Path:
    return src / f"{MANUSCRIPT}-page{n}.jpg"


def _src_ref(src: Path, n: str) -> Path:
    return src / f"{MANUSCRIPT}-page{n}-transcription.txt"


def build(source_dir: str, out_root: str) -> dict:
    src = Path(source_dir)
    out = Path(out_root)

    for n in SPLITS["dev"]:
        dst = out / "corpus" / "dev"
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_src_img(src, n), dst / f"page-{n}.jpg")
        shutil.copyfile(_src_ref(src, n), dst / f"page-{n}.txt")

    for split in ("val", "test"):
        imgs = out / "corpus" / split / "images"
        refs = out / "corpus" / split / "refs"
        imgs.mkdir(parents=True, exist_ok=True)
        refs.mkdir(parents=True, exist_ok=True)
        for n in SPLITS[split]:
            shutil.copyfile(_src_img(src, n), imgs / f"page-{n}.jpg")
            shutil.copyfile(_src_ref(src, n), refs / f"page-{n}.txt")

    manifest = {
        "manuscript": MANUSCRIPT,
        "excluded": ["002"],
        "splits": SPLITS,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "splits.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: build_splits.py SOURCE_DIR OUT_ROOT", file=sys.stderr)
        sys.exit(1)
    m = build(sys.argv[1], sys.argv[2])
    print(json.dumps(m, indent=2))
