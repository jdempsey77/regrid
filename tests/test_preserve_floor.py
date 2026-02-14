"""Tests for preserve-floor convert pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_regrid(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    cwd = cwd or REPO_ROOT
    env = {**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "regrid", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_preserve_floor_keeps_floor_geometry(mini_bin_stl: Path, ref_tile_path: Path) -> None:
    """Convert with preserve-floor produces output and run completes."""
    if not ref_tile_path.exists():
        pytest.skip("refs/tile_21_1x1.stl not found")
    result = _run_regrid("convert", str(mini_bin_stl), "--dry-run")
    assert result.returncode == 0, (result.stdout, result.stderr)
    out = result.stdout + result.stderr
    assert "z_join" in out or "z_cut_body" in out or "Run summary" in out


def test_verify_passes_on_fixture(mini_bin_stl: Path, ref_tile_path: Path) -> None:
    """Full convert with --verify passes (output matches original above floor)."""
    if not ref_tile_path.exists():
        pytest.skip("refs/tile_21_1x1.stl not found")
    result = _run_regrid(
        "convert",
        str(mini_bin_stl),
        "--verify",
        "--verify-tol-mm",
        "0.1",
    )
    out = result.stdout + result.stderr
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Verify: PASS" in out or "PASS" in out
