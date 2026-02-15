# Samples

- **`sample_42_1x1.stl`** — Simple 42×42×10 mm box (1×1 at 42 mm pitch). Used in the README Quickstart and Golden run.

- **`gridfinity_bin_42mm.stl`** — Realistic Gridfinity bin with proper floor, walls, and base section. 42×42×15 mm with 2mm walls, 2mm floor thickness, and interior floor at 7mm height.

Regenerate samples:

```bash
# Simple box
python scripts/generate_sample_bin.py

# Realistic bin with floor and walls
python scripts/generate_gridfinity_bin.py
```
