"""Tests for floor detection."""

from __future__ import annotations

import trimesh

from regrid.detect import detect_floor_z, detect_floor_z_with_confidence


def test_floor_detection_returns_value() -> None:
    """detect_floor_z returns a float for a simple box (clear horizontal section)."""
    import numpy as np
    box = trimesh.creation.box(extents=[42, 42, 10])
    # Box is centered at origin (z from -5 to 5), shift to positive z
    box.vertices += np.array([0, 0, 5])  # Now z from 0 to 10
    z_floor = detect_floor_z(box)
    assert z_floor is not None
    assert 0.5 <= z_floor <= 10.0


def test_floor_detection_with_confidence() -> None:
    """detect_floor_z_with_confidence returns (z, stability)."""
    import numpy as np
    box = trimesh.creation.box(extents=[30, 30, 8])
    box.vertices += np.array([0, 0, 4])  # Shift to positive z
    z_floor, stability = detect_floor_z_with_confidence(box)
    assert z_floor is not None
    assert 0 <= stability <= 1.0
