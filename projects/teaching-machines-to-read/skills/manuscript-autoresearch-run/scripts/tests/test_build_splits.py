import json
from pathlib import Path

import build_splits


def _make_fake_corpus(src: Path):
    """One .jpg + one -transcription.txt for every page in all three splits."""
    src.mkdir(parents=True, exist_ok=True)
    for pages in build_splits.SPLITS.values():
        for n in pages:
            (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"JPEGDATA")
            (src / f"sedley-ms534-page{n}-transcription.txt").write_text(f"ref {n}")


def test_splits_are_13_each_and_disjoint():
    s = build_splits.SPLITS
    assert [len(s["dev"]), len(s["val"]), len(s["test"])] == [13, 13, 13]
    allp = s["dev"] + s["val"] + s["test"]
    assert len(allp) == len(set(allp)) == 39
    assert "002" not in allp  # flyleaf excluded


def test_build_copies_isolated_layout(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    _make_fake_corpus(src)

    manifest = build_splits.build(str(src), str(out))

    # val images present, val refs present, but images dir has NO refs (isolation)
    val_imgs = sorted(p.name for p in (out / "corpus/val/images").glob("*"))
    val_refs = sorted(p.name for p in (out / "corpus/val/refs").glob("*"))
    assert val_imgs == [f"page-{n}.jpg" for n in build_splits.SPLITS["val"]]
    assert val_refs == [f"page-{n}.txt" for n in build_splits.SPLITS["val"]]
    assert not list((out / "corpus/val/images").glob("*.txt"))

    # dev keeps image + ref together (study pool)
    assert (out / "corpus/dev/page-003.jpg").exists()
    assert (out / "corpus/dev/page-003.txt").exists()

    # manifest written and matches
    written = json.loads((out / "splits.json").read_text())
    assert written == manifest
    assert written["splits"] == build_splits.SPLITS
