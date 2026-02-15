#!/usr/bin/env python3
"""
Test harness runner for regrid end-to-end tests.
Provides clear output and summary of test results.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = REPO_ROOT / "tests" / "test_e2e.py"


def print_header(msg: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"  {msg}")
    print(f"{'=' * 80}\n")


def print_section(msg: str) -> None:
    """Print a formatted section."""
    print(f"\n{'-' * 80}")
    print(f"  {msg}")
    print(f"{'-' * 80}\n")


def check_dependencies() -> dict[str, bool]:
    """Check which optional dependencies are installed."""
    deps = {}
    
    for pkg in ["pytest", "trimesh", "numpy", "manifold3d", "rtree", "scipy"]:
        try:
            __import__(pkg)
            deps[pkg] = True
        except ImportError:
            deps[pkg] = False
    
    return deps


def run_test_suite(
    test_pattern: str | None = None,
    verbose: bool = True,
    show_output: bool = True,
) -> int:
    """
    Run the test suite and return exit code.
    
    Args:
        test_pattern: Specific test pattern (e.g., "TestFloorCommand")
        verbose: Show verbose pytest output
        show_output: Show test output in real-time
    """
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_pattern:
        cmd.append(f"{TEST_FILE}::{test_pattern}")
    else:
        cmd.append(str(TEST_FILE))
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    if show_output:
        cmd.append("-s")
    
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def main() -> int:
    """Main test harness."""
    print_header("ReGrid End-to-End Test Harness")
    
    # Check dependencies
    print_section("Checking Dependencies")
    deps = check_dependencies()
    
    for pkg, installed in deps.items():
        status = "✓ Installed" if installed else "✗ Missing"
        print(f"  {pkg:15s} {status}")
    
    # Warn about missing optional dependencies
    if not deps.get("rtree") or not deps.get("scipy"):
        print("\n  ⚠️  Warning: rtree/scipy not installed - verify tests will be skipped")
        print("     Install with: pip install -e \".[test,verify]\"")
    
    # Check for sample files
    print_section("Checking Sample Files")
    samples_dir = REPO_ROOT / "samples"
    refs_dir = REPO_ROOT / "refs"
    
    sample_42 = samples_dir / "sample_42_1x1.stl"
    ref_tile = refs_dir / "tile_21_1x1.stl"
    
    print(f"  Sample 42mm: {'✓ Found' if sample_42.exists() else '✗ Missing'} - {sample_42}")
    print(f"  Ref tile:    {'✓ Found' if ref_tile.exists() else '✗ Missing'} - {ref_tile}")
    
    if not sample_42.exists() or not ref_tile.exists():
        print("\n  ⚠️  Warning: Missing sample files - some tests will be skipped")
    
    # Parse command line args
    test_pattern = None
    if len(sys.argv) > 1:
        test_pattern = sys.argv[1]
        print_section(f"Running Test Pattern: {test_pattern}")
    else:
        print_section("Running All End-to-End Tests")
    
    # Run tests
    exit_code = run_test_suite(test_pattern=test_pattern)
    
    # Print summary
    print_section("Test Summary")
    if exit_code == 0:
        print("  ✓ All tests passed!")
    else:
        print(f"  ✗ Tests failed (exit code: {exit_code})")
    
    print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
