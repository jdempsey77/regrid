#!/usr/bin/env python3
"""
Generate a minimal 42×42 mm (1×1 Gridfinity footprint) example STL for samples/.

Usage (from repo root):
    python scripts/generate_sample_bin.py

Writes: samples/sample_42_1x1.stl
"""
from __future__ import annotations

from pathlib import Path

def main() -> None:
    try:
        import trimesh
    except ImportError:
        raise SystemExit("trimesh required: pip install trimesh") from None

    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sample_42_1x1.stl"

    # 42×42×10 mm box — 1×1 at 42 mm pitch; floor detection will find the bottom face
    box = trimesh.creation.box(extents=[42.0, 42.0, 10.0])
    box.export(out_path.as_posix())
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
