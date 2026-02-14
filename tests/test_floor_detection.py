"""Tests for floor detection."""

from __future__ import annotations

import trimesh

from regrid.detect import detect_floor_z, detect_floor_z_with_confidence


def test_floor_detection_returns_value() -> None:
    """detect_floor_z returns a float for a simple box (clear horizontal section)."""
    box = trimesh.creation.box(extents=[42, 42, 10])  # z from 0 to 10
    z_floor = detect_floor_z(box)
    assert z_floor is not None
    assert 0.5 <= z_floor <= 10.0


def test_floor_detection_with_confidence() -> None:
    """detect_floor_z_with_confidence returns (z, stability)."""
    box = trimesh.creation.box(extents=[30, 30, 8])
    z_floor, stability = detect_floor_z_with_confidence(box)
    assert z_floor is not None
    assert 0 <= stability <= 1.0
