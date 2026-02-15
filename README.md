# ReGrid

[![tests](https://github.com/jdempsey77/regrid/actions/workflows/tests.yml/badge.svg)](https://github.com/jdempsey77/regrid/actions/workflows/tests.yml)

**Same bin. New grid.** ReGrid converts Gridfinity bins between grid pitches while preserving geometry above the interior floor plane—only the underside interface changes.

## Quickstart

From the repo root (after cloning and `source .venv/bin/activate` or similar):

```bash
pip install -e .
regrid floor samples/sample_42_1x1.stl
regrid convert samples/sample_42_1x1.stl --export-debug
```

Optional: run conversion with verification (requires the verify extra):

```bash
pip install -e ".[verify]"
regrid convert samples/sample_42_1x1.stl --verify
```

You need the reference tile in place first—see [Reference tile (required)](#reference-tile-required) below.

---

## Reference tile (required)

The converter uses a single **canonical 21 mm 1×1 interface tile** at `refs/tile_21_1x1.stl`. This repo is set up to **commit that file** so clone → install → run works with no extra steps.

- **What it is:** The standard Gridfinity 21 mm pitch 1×1 base tile used to build the new underside. Same geometry you’d get from a 1×1 base in [Gridfinity Generator](https://gridfinity.xyz/) or equivalent at 21 mm.
- **Provenance and licensing:** Obtain it from a source you’re allowed to use (e.g. export from gridfinitygenerator.com or your own model). The ReGrid repo does not assert license on the tile; keep any attribution or license that applies to the source you use. Once you have the STL, save it as `refs/tile_21_1x1.stl` and commit it.
- **If the file is missing:** Export a 21 mm 1×1 base from [gridfinitygenerator.com](https://gridfinity.xyz/) (or equivalent), save it as **`refs/tile_21_1x1.stl`** in the repo root, then commit. Tests that need the tile skip with: `refs/tile_21_1x1.stl not found`.

---

## What ReGrid Does

- **Identical geometry above the interior floor** — Walls, arch, and floor surface are unchanged.
- **Only the underside interface changes** — A new grid base is built from a reference tile and unioned below the floor plane.
- **Exact outer footprint preserved** — The slab is cropped to the body footprint so there is no overhang or shift.

Default behavior (preserve-floor mode) auto-detects the interior floor height, cuts the body just below it (with a small epsilon so coplanar floor faces are kept), and builds the new interface underneath.

---

## How It Works

1. **Detect interior floor** — Scan the mesh from the bottom upward; find the first horizontal plane where cross-section area reaches ~90% of max and stays stable for a few steps.
2. **Cut below the plane** — Body = everything *above* `z_cut_body` (floor plane minus a small epsilon so the floor is kept).
3. **Insert new grid interface** — Tile the reference slice to the target pitch, align to the body, place its top just below the join plane with a small overlap.
4. **Crop to footprint** — Intersect the slab with a box matching the body’s XY bounds so the footprint is preserved.
5. **Union** — Union body and slab. Optional **verify** mode samples surfaces above the join plane and checks nearest-neighbor distances to confirm the output matches the original.

---

## Installation

From the repo root (so the reference tile path resolves):

```bash
pip install -e .
```

Requires Python 3.9+. Core deps: `numpy`, `trimesh`, `manifold3d`.

**Verify requires extras.** The `--verify` flag needs the `rtree` dependency:

```bash
pip install -e ".[verify]"
# or with tests: pip install -e ".[test,verify]"
```

See [Reference tile (required)](#reference-tile-required) above.

---

## Golden run

Using the included 42×42 mm example (`samples/sample_42_1x1.stl`), a typical run looks like this.

```bash
regrid convert samples/sample_42_1x1.stl --export-debug
```

You should see log lines along these lines (exact numbers depend on the mesh):

- `Detected interior floor at z_floor=... mm (join plane); cutting body above z_cut_body=... mm`
- `Exported debug meshes to .../debug/`
- `Wrote: out/...  (NxM @ 42.0 mm => NxM @ 21.0 mm)`
- **Run summary:** `zmin`, `z_join (floor plane)`, `z_cut_body`, `effective_replace_height`, `footprint preserved true`

Debug outputs are written under **`debug/`** (from the current working directory, usually repo root): `body_only.stl`, `slab_only.stl`, `pre_union.stl`. With `regrid floor` you also get `debug/floor_plane.stl`. Do not commit `debug/` or `out/`—they are in `.gitignore`.

---

## Usage

```bash
# Convert a bin (preserve-floor by default)
regrid convert bin.stl

# Convert and verify geometry above floor matches original
regrid convert bin.stl --verify

# Detect floor plane and export debug/floor_plane.stl
regrid floor bin.stl
regrid floor bin.stl -v   # print area stability (confidence)
```

**Convert options:**  
`--no-preserve-floor` — Use fixed replace-height instead of auto floor.  
`--replace-height-mm` — Height of bottom region when not preserving floor (default 7).  
`--floor-epsilon-mm` — Cut body this far below floor plane to keep floor faces (default 0.1).  
`--verify` — After writing output, check that geometry above the floor plane matches (requires `pip install "regrid[verify]"`).  
`--verify-tol-mm` — Max allowed nearest-neighbor distance for verify (default 0.05).  
`--export-debug` — Export body_only, slab_only, pre_union to `debug/`.  
`--dry-run` — Skip union; only export debug meshes.  
`--out`, `--modules`, `--rotate`, `--pitch-src`, `--pitch-dst`, etc.

---

## Guarantees

- **z_join** — The plane where body and slab meet (detected floor or fixed cut height).
- **z_cut_body** — The plane used to cut the body (`z_join - floor_epsilon_mm` in preserve-floor mode so coplanar floor faces are kept).
- **Floor epsilon** — Prevents the boolean cut from dropping the floor; increase to 0.15 if the floor is still missing.
- **Verify mode** — Samples ~10k points on original and output above `z_join`, computes nearest-neighbor distances both ways; fails if max distance &gt; tolerance. Use `--verify` to make the guarantee provable.

---

## Troubleshooting

- **Floor detection failed** — No stable floor plane found in the first 15 mm. Use `--no-preserve-floor` and/or `--replace-height-mm`, or check that the mesh has a clear interior floor.
- **Missing interior floor** — Output has no floor. Increase `--floor-epsilon-mm` to 0.15 so the body cut stays below the floor and keeps floor faces.
- **Boolean errors** — Meshes may be non-manifold. Run with `--dry-run` or `--export-debug` and inspect `debug/body_only.stl` and `debug/slab_only.stl`.
- **Module detection failed** — Footprint doesn’t match the expected pitch grid. Use `--modules NxM` (e.g. `5x5`) to override.
- **Reference tile mismatch** — Ensure `refs/tile_21_1x1.stl` is a 1×1 tile at the target pitch (e.g. 21 mm).

---

## Tests

```bash
pip install -e ".[test,verify]"
pytest tests/ -v
```

**End-to-end test harness:**
```bash
# Run all E2E tests
make test-e2e

# Or use the test runner
python scripts/run_e2e_tests.py

# Run specific test class
python scripts/run_e2e_tests.py TestConvertBasic
```

See `tests/TEST_HARNESS.md` for complete documentation.

Fixtures: `tests/fixtures/` (mini_bin.stl created by conftest if missing) or programmatic geometry. Tests that require `refs/tile_21_1x1.stl` skip cleanly if the file is absent. Floor detection and preserve-floor tests run without the ref; convert/verify tests need it.

Alternatively use the Makefile: `make venv`, then `source .venv/bin/activate`, `make install`, `make test`.

---

## License

MIT. See [LICENSE](LICENSE).
