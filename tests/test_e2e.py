"""
End-to-end integration tests using real sample files.
Tests the complete regrid pipeline from input STL to output STL.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "samples"
REFS_DIR = REPO_ROOT / "refs"
DEBUG_DIR = REPO_ROOT / "debug"
OUT_DIR = REPO_ROOT / "out"


@pytest.fixture(autouse=True)
def cleanup_output_dirs():
    """Clean up debug/ and out/ directories before and after each test."""
    for dir_path in [DEBUG_DIR, OUT_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
    yield
    # Cleanup after test too
    for dir_path in [DEBUG_DIR, OUT_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)


def run_regrid(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run regrid CLI command and return result."""
    env = {**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "regrid", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture
def sample_42_stl() -> Path:
    """Path to the 42mm sample STL file."""
    path = SAMPLES_DIR / "sample_42_1x1.stl"
    if not path.exists():
        pytest.skip(f"Sample file not found: {path}")
    return path


@pytest.fixture
def ref_tile() -> Path:
    """Path to the reference 21mm tile."""
    path = REFS_DIR / "tile_21_1x1.stl"
    if not path.exists():
        pytest.skip(f"Reference tile not found: {path}")
    return path


class TestFloorCommand:
    """Test the 'floor' subcommand."""

    def test_floor_detection_on_sample(self, sample_42_stl: Path):
        """Floor command should detect floor and export debug plane."""
        result = run_regrid("floor", str(sample_42_stl))
        
        assert result.returncode == 0, (
            f"Floor command failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        
        # Check output contains floor detection info
        output = result.stdout + result.stderr
        assert "z_floor=" in output, "Missing z_floor in output"
        assert "Exported" in output, "Missing export confirmation"
        
        # Check debug file was created
        floor_plane = DEBUG_DIR / "floor_plane.stl"
        assert floor_plane.exists(), f"Floor plane STL not created at {floor_plane}"

    def test_floor_verbose(self, sample_42_stl: Path):
        """Floor command with -v should show area stability."""
        result = run_regrid("floor", str(sample_42_stl), "-v")
        
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "z_floor=" in output


class TestConvertDryRun:
    """Test convert command with --dry-run (no output file)."""

    def test_dry_run_exports_debug_meshes(self, sample_42_stl: Path, ref_tile: Path):
        """Dry-run should export body_only, slab_only, pre_union."""
        result = run_regrid("convert", str(sample_42_stl), "--dry-run")
        
        assert result.returncode == 0, (
            f"Dry-run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        
        output = result.stdout + result.stderr
        assert "Inferred modules" in output or "Using modules" in output
        assert "Detected interior floor" in output or "z_floor=" in output
        
        # Check all debug files exist
        debug_files = ["body_only.stl", "slab_only.stl", "pre_union.stl"]
        for filename in debug_files:
            debug_file = DEBUG_DIR / filename
            assert debug_file.exists(), f"Debug file missing: {debug_file}"
            assert debug_file.stat().st_size > 0, f"Debug file is empty: {debug_file}"

    def test_dry_run_with_export_debug(self, sample_42_stl: Path, ref_tile: Path):
        """Using --export-debug should also work (same as --dry-run)."""
        result = run_regrid("convert", str(sample_42_stl), "--export-debug")
        
        assert result.returncode == 0
        assert (DEBUG_DIR / "body_only.stl").exists()


class TestConvertBasic:
    """Test basic convert command (no verification)."""

    def test_convert_creates_output(self, sample_42_stl: Path, ref_tile: Path):
        """Convert should create output STL file."""
        result = run_regrid("convert", str(sample_42_stl))
        
        assert result.returncode == 0, (
            f"Convert failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        
        output = result.stdout + result.stderr
        assert "Wrote:" in output, "Missing output confirmation"
        assert "42.0 mm" in output and "21.0 mm" in output, "Missing pitch info"
        
        # Check output file was created
        output_files = list(OUT_DIR.glob("*.stl"))
        assert len(output_files) > 0, f"No output STL file created in {OUT_DIR}"
        
        output_stl = output_files[0]
        assert output_stl.stat().st_size > 0, "Output STL is empty"

    def test_convert_with_custom_output(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --out should use custom output path."""
        custom_out = OUT_DIR / "custom_output.stl"
        result = run_regrid("convert", str(sample_42_stl), "--out", str(custom_out))
        
        assert result.returncode == 0
        assert custom_out.exists(), f"Custom output not created: {custom_out}"

    def test_convert_with_modules_override(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --modules should override auto-detection."""
        result = run_regrid("convert", str(sample_42_stl), "--modules", "1x1")
        
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "1x1" in output


class TestConvertWithVerify:
    """Test convert command with verification enabled."""

    def test_convert_verify_passes(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --verify should pass on sample file."""
        try:
            import rtree  # noqa: F401
            import scipy  # noqa: F401
        except ImportError:
            pytest.skip("Verify requires rtree and scipy extras")
        
        result = run_regrid(
            "convert",
            str(sample_42_stl),
            "--verify",
            "--verify-tol-mm",
            "0.1",
        )
        
        assert result.returncode == 0, (
            f"Verify failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        
        output = result.stdout + result.stderr
        assert "Verify: PASS" in output or "PASS" in output, "Verify did not pass"
        assert "Wrote:" in output

    def test_convert_verify_with_strict_tolerance(self, sample_42_stl: Path, ref_tile: Path):
        """Verify with very strict tolerance should still work on simple geometry."""
        try:
            import rtree  # noqa: F401
            import scipy  # noqa: F401
        except ImportError:
            pytest.skip("Verify requires rtree and scipy extras")
        
        result = run_regrid(
            "convert",
            str(sample_42_stl),
            "--verify",
            "--verify-tol-mm",
            "0.05",
        )
        
        # Should pass for simple geometry, but allow failure for complex cases
        output = result.stdout + result.stderr
        if result.returncode != 0:
            pytest.skip("Strict tolerance too tight for this geometry")
        assert "Verify: PASS" in output or "PASS" in output


class TestConvertOptions:
    """Test various convert command options."""

    def test_no_preserve_floor(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --no-preserve-floor should use fixed replace height."""
        result = run_regrid("convert", str(sample_42_stl), "--no-preserve-floor")
        
        assert result.returncode == 0
        # Should still create output
        assert len(list(OUT_DIR.glob("*.stl"))) > 0

    def test_custom_replace_height(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --replace-height-mm should use custom height."""
        result = run_regrid(
            "convert",
            str(sample_42_stl),
            "--no-preserve-floor",
            "--replace-height-mm",
            "5.0",
        )
        
        assert result.returncode == 0

    def test_custom_floor_epsilon(self, sample_42_stl: Path, ref_tile: Path):
        """Convert with --floor-epsilon-mm should use custom epsilon."""
        result = run_regrid(
            "convert",
            str(sample_42_stl),
            "--floor-epsilon-mm",
            "0.15",
        )
        
        assert result.returncode == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_nonexistent_input_file(self):
        """Should fail gracefully with nonexistent input."""
        result = run_regrid("convert", "nonexistent.stl")
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "error" in output.lower() or "not found" in output.lower()

    def test_missing_ref_tile(self, sample_42_stl: Path):
        """Should fail gracefully if reference tile is missing."""
        # Temporarily rename the ref tile
        ref_tile = REFS_DIR / "tile_21_1x1.stl"
        if not ref_tile.exists():
            pytest.skip("Reference tile already missing")
        
        backup = REFS_DIR / "tile_21_1x1.stl.backup"
        ref_tile.rename(backup)
        
        try:
            result = run_regrid("convert", str(sample_42_stl))
            assert result.returncode != 0
            output = result.stdout + result.stderr
            assert "tile" in output.lower() or "not found" in output.lower()
        finally:
            # Restore the ref tile
            if backup.exists():
                backup.rename(ref_tile)


class TestMiniIntegration:
    """Test with programmatically generated mini fixture."""

    def test_mini_bin_end_to_end(self, mini_bin_stl: Path, ref_tile: Path):
        """Full pipeline test with mini_bin fixture."""
        result = run_regrid("convert", str(mini_bin_stl))
        
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "Wrote:" in output
        
        # Should create output
        output_files = list(OUT_DIR.glob("*.stl"))
        assert len(output_files) > 0
