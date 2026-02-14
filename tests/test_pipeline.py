"""
Tests: dry-run and verify on sample fixtures.
Run from repo root: pytest tests/ -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_regrid(
    input_stl: Path,
    *extra_args: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    cwd = cwd or REPO_ROOT
    env = {"PYTHONPATH": str(REPO_ROOT / "src")}
    cmd = [
        sys.executable,
        "-m",
        "regrid",
        str(input_stl),
        *extra_args,
    ]
    return subprocess.run(
        cmd,
        cwd=cwd,
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.skip(reason="post_it_holder_stl fixture not available - add real STL file to test")
def test_dry_run_post_it_holder(post_it_holder_stl: Path) -> None:
    """Dry-run on Post-It Holder must succeed and export debug meshes."""
    result = _run_regrid(post_it_holder_stl, "convert", "--dry-run")
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Inferred modules" in result.stdout or "Using modules" in result.stdout
    assert "z_floor=" in result.stdout or "Detected interior floor" in result.stdout
    debug_dir = REPO_ROOT / "debug"
    assert (debug_dir / "body_only.stl").exists()
    assert (debug_dir / "slab_only.stl").exists()
    assert (debug_dir / "pre_union.stl").exists()


@pytest.mark.skip(reason="rugged_organizer_stl fixture not available - add real STL file to test")
def test_dry_run_rugged_organizer(rugged_organizer_stl: Path) -> None:
    """Dry-run on Rugged Organizer must succeed."""
    result = _run_regrid(rugged_organizer_stl, "convert", "--dry-run")
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Exported debug meshes" in result.stdout or "Dry run" in result.stdout


@pytest.mark.skip(reason="post_it_holder_stl fixture not available - add real STL file to test")
def test_verify_post_it_holder(post_it_holder_stl: Path) -> None:
    """Full run + verify on Post-It Holder must PASS (requires rtree)."""
    result = _run_regrid(
        post_it_holder_stl,
        "convert",
        "--verify",
        "--verify-tol-mm",
        "0.1",
    )
    out = result.stdout + result.stderr
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Wrote:" in out
    assert "Verify: PASS" in out or "PASS" in out
    out_stl = REPO_ROOT / "out" / "Gridfinity Post-It Holder_21mm.stl"
    assert out_stl.exists()


@pytest.mark.skip(reason="rugged_organizer_stl fixture not available - add real STL file to test")
def test_verify_rugged_organizer(rugged_organizer_stl: Path) -> None:
    """Full run + verify on Rugged Organizer must PASS (requires rtree)."""
    result = _run_regrid(
        rugged_organizer_stl,
        "convert",
        "--verify",
        "--verify-tol-mm",
        "0.1",
    )
    out = result.stdout + result.stderr
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Verify: PASS" in out or "PASS" in out


@pytest.mark.skip(reason="post_it_holder_stl fixture not available - add real STL file to test")
def test_floor_subcommand(post_it_holder_stl: Path) -> None:
    """Floor subcommand must print z_floor and export floor_plane.stl."""
    env = {"PYTHONPATH": str(REPO_ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "regrid", "floor", str(post_it_holder_stl)],
        cwd=REPO_ROOT,
        env={**__import__("os").environ, **env},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "z_floor=" in result.stdout
    assert "Exported" in result.stdout
    assert (REPO_ROOT / "debug" / "floor_plane.stl").exists()
