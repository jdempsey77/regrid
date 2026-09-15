# regrid — Claude Code notes

## What this is

A Python CLI (`pip install -e .` → `regrid`) that converts Gridfinity bins
between grid pitches: geometry above the interior floor plane is preserved
exactly, only the underside interface is rebuilt at the new pitch. Not a
model project despite living alongside 3D-printing work elsewhere in this
account — it's a real Python package with tests and CI, which is why it
lives in `tools/` rather than `~/3d`.

## How to run it

    pip install -e .
    regrid floor samples/sample_42_1x1.stl
    regrid convert samples/sample_42_1x1.stl --export-debug
    pip install -e ".[verify]"    # needed for --verify (adds rtree)
    regrid convert samples/sample_42_1x1.stl --verify

Requires the reference tile at `refs/tile_21_1x1.stl` (and
`tile_42_1x1.stl`), which **is** committed to this repo — both present.
Must run from the repo root so that path resolves.

## How to test it

    pip install -e ".[test,verify]"
    pytest tests/ -v

    make test-e2e                          # end-to-end harness
    python scripts/run_e2e_tests.py        # same, or target one class

CI (`.github/workflows/tests.yml`) runs `pytest tests/ -v --tb=short` on
every push/PR to `main`/`master` — last 3 runs on `main` all `success` per
`gh run list`. Tests needing `refs/tile_21_1x1.stl` skip cleanly if it's
absent; floor-detection and preserve-floor tests don't need it.

## Where it deploys

Nowhere — a CLI tool, installed locally (`pip install -e .`), not a
service.

## Secrets

None. No `.sops.yaml`, no credentials — pure geometry processing.

## Gotchas

- The reference tile's provenance/license is the user's responsibility —
  the README is explicit that ReGrid "does not assert license on the
  tile"; whoever exports `refs/tile_21_1x1.stl` from Gridfinity Generator
  (or elsewhere) keeps whatever attribution/license applies to that
  source. Don't treat the committed tile as freely re-licensable.
- `debug/` and `out/` are gitignored on purpose — don't commit debug mesh
  exports (`body_only.stl`, `slab_only.stl`, `pre_union.stl`,
  `floor_plane.stl`) or conversion output.
- Floor detection scans bottom-up for the first stable ~90%-max
  cross-section plane in the first 15mm — if that fails ("Floor detection
  failed"), the fix is `--no-preserve-floor` + `--replace-height-mm`, not a
  tolerance tweak. A *missing* floor in otherwise-successful output is a
  different problem (`--floor-epsilon-mm` too small, default 0.1 → try
  0.15) — the README's Troubleshooting section distinguishes these two
  failure modes, don't conflate them.
