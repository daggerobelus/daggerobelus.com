from pathlib import Path

import assemble_materials
import build_splits


def _seed(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    for n in build_splits.SPLITS["val"] + build_splits.SPLITS["test"] + build_splits.SPLITS["dev"]:
        (src / f"sedley-ms534-page{n}.jpg").write_bytes(b"J")
        (src / f"sedley-ms534-page{n}-transcription.txt").write_text(f"ref {n}")
    root = tmp_path / "root"
    build_splits.build(str(src), str(root))
    return root


def test_blind_arm_images_only(tmp_path):
    root = _seed(tmp_path)
    dest = tmp_path / "mat_blind"
    pages = assemble_materials.assemble(str(root), "val", "blind", str(dest))
    assert pages == build_splits.SPLITS["val"]
    assert sorted(p.name for p in dest.glob("*.jpg")) == [f"page-{n}.jpg" for n in pages]
    assert list(dest.glob("*.txt")) == []          # BLIND: no references


def test_faithful_arm_includes_refs(tmp_path):
    root = _seed(tmp_path)
    dest = tmp_path / "mat_faithful"
    pages = assemble_materials.assemble(str(root), "val", "faithful", str(dest))
    assert sorted(p.name for p in dest.glob("*.jpg")) == [f"page-{n}.jpg" for n in pages]
    assert sorted(p.name for p in dest.glob("*.txt")) == [f"page-{n}.txt" for n in pages]  # refs present
