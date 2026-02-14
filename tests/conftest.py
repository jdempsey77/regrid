"""Pytest fixtures. Uses tests/fixtures/ or programmatic geometry."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
SRC_DIR = REPO_ROOT / "src"
REFS_DIR = REPO_ROOT / "refs"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def mini_bin_stl(fixtures_dir: Path) -> Path:
    """Create a minimal box STL for tests (42x42x10 mm) if not present."""
    path = fixtures_dir / "mini_bin.stl"
    if path.exists():
        return path
    import trimesh
    box = trimesh.creation.box(extents=[42, 42, 10])
    box.export(path.as_posix())
    return path


@pytest.fixture(scope="session")
def ref_tile_path() -> Path:
    return REFS_DIR / "tile_21_1x1.stl"


@pytest.fixture(autouse=True)
def _add_src_to_path() -> None:
    src = str(SRC_DIR)
    if src not in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        os.environ["PYTHONPATH"] = os.pathsep.join([src, os.environ.get("PYTHONPATH", "")])
