"""
Module detection: parse and infer Gridfinity module counts from mesh footprint.
Floor detection: find interior floor plane via horizontal cross-section area.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import trimesh

logger = logging.getLogger(__name__)

_TOL_CHAIN = 1e-4


def _cross_section_area_at_z(mesh: "trimesh.Trimesh", z: float) -> float:
    """Compute total area of horizontal cross-section at z. Returns 0.0 if no section or on error."""
    import trimesh.intersections

    try:
        lines = trimesh.intersections.mesh_plane(
            mesh,
            plane_origin=np.array([0.0, 0.0, z]),
            plane_normal=np.array([0.0, 0.0, 1.0]),
        )
    except Exception:
        return 0.0
    if lines is None or len(lines) == 0:
        return 0.0
    lines = np.asarray(lines)
    if lines.ndim != 3 or lines.shape[1] != 2 or lines.shape[2] != 3:
        return 0.0
    segs = lines[:, :, :2].reshape(-1, 2, 2)
    return _polygon_area_from_segments(segs)


def _polygon_area_from_segments(segs: np.ndarray) -> float:
    """Chain (n, 2, 2) XY segments into closed loops; return sum of absolute polygon areas."""
    if len(segs) == 0:
        return 0.0
    tol = _TOL_CHAIN
    used = np.zeros(len(segs), dtype=bool)
    total = 0.0
    for start in range(len(segs)):
        if used[start]:
            continue
        loop = list(segs[start].tolist())
        used[start] = True
        head = np.array(loop[0])
        tail = np.array(loop[-1])
        while True:
            found = False
            for i in range(len(segs)):
                if used[i]:
                    continue
                a, b = segs[i][0], segs[i][1]
                if np.linalg.norm(tail - a) <= tol:
                    loop.append(b.tolist())
                    tail = b
                    used[i] = True
                    found = True
                    break
                if np.linalg.norm(tail - b) <= tol:
                    loop.append(a.tolist())
                    tail = a
                    used[i] = True
                    found = True
                    break
            if not found:
                break
        if len(loop) >= 3 and np.linalg.norm(np.array(loop[-1]) - head) <= tol:
            pts = np.array(loop[:-1])
            total += abs(_shoelace_area(pts))
    return total


def _shoelace_area(pts: np.ndarray) -> float:
    """Signed area of polygon (pts is (n, 2) XY)."""
    if len(pts) < 3:
        return 0.0
    x, y = pts[:, 0], pts[:, 1]
    return float(0.5 * (np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


def detect_floor_z(
    mesh: "trimesh.Trimesh",
    z_search_max: float = 15.0,
    step: float = 0.2,
    area_ratio: float = 0.9,
    stable_steps: int = 3,
) -> float | None:
    """
    Detect interior floor plane Z by horizontal cross-section area.
    Scans from zmin+0.5mm upward; returns first z where section area >= area_ratio * max_area
    for stable_steps consecutive samples. Returns None if no stable floor found.
    """
    zmin = float(mesh.bounds[0, 2])
    z_start = zmin + 0.5
    z_end = min(zmin + z_search_max, float(mesh.bounds[1, 2]) - 0.01)
    if z_end <= z_start:
        return None
    z_values = np.arange(z_start, z_end, step)
    areas = []
    for z in z_values:
        areas.append(_cross_section_area_at_z(mesh, float(z)))
    areas = np.array(areas)
    if len(areas) == 0 or np.max(areas) <= 0:
        return None
    max_area = float(np.max(areas))
    threshold = area_ratio * max_area
    for i in range(len(areas) - stable_steps + 1):
        window = areas[i : i + stable_steps]
        if np.all(window >= threshold):
            return float(z_values[i])
    return None


def detect_floor_z_with_confidence(
    mesh: "trimesh.Trimesh",
    z_search_max: float = 15.0,
    step: float = 0.2,
    area_ratio: float = 0.9,
    stable_steps: int = 3,
) -> tuple[float | None, float]:
    """
    Like detect_floor_z but also returns area stability (min area in stable window / max_area).
    Returns (z_floor or None, stability in [0,1] or 0 if not found).
    """
    zmin = float(mesh.bounds[0, 2])
    z_start = zmin + 0.5
    z_end = min(zmin + z_search_max, float(mesh.bounds[1, 2]) - 0.01)
    if z_end <= z_start:
        return None, 0.0
    z_values = np.arange(z_start, z_end, step)
    areas = np.array([_cross_section_area_at_z(mesh, float(z)) for z in z_values])
    if len(areas) == 0 or np.max(areas) <= 0:
        return None, 0.0
    max_area = float(np.max(areas))
    threshold = area_ratio * max_area
    for i in range(len(areas) - stable_steps + 1):
        window = areas[i : i + stable_steps]
        if np.all(window >= threshold):
            stability = float(np.min(window) / max_area) if max_area > 0 else 0.0
            return float(z_values[i]), stability
    return None, 0.0


def mesh_bounds_xy(mesh: "trimesh.Trimesh") -> tuple[float, float, float, float]:
    """Return (minx, maxx, miny, maxy) from mesh XY bounds."""
    b = mesh.bounds
    return float(b[0, 0]), float(b[1, 0]), float(b[0, 1]), float(b[1, 1])


def mesh_min_z(mesh: "trimesh.Trimesh") -> float:
    """Return minimum Z coordinate of mesh."""
    return float(mesh.bounds[0, 2])


def mesh_center_xy(mesh: "trimesh.Trimesh") -> np.ndarray:
    """Return XY center of mesh as [cx, cy]."""
    b = mesh.bounds
    cx = (b[0, 0] + b[1, 0]) / 2.0
    cy = (b[0, 1] + b[1, 1]) / 2.0
    return np.array([cx, cy])


def parse_modules(s: str) -> tuple[int, int]:
    """Parse module string like '5x5' into (n, m). Raises ValueError if invalid."""
    s = s.lower().strip()
    if "x" not in s:
        raise ValueError(
            f"Invalid --modules format: '{s}'. Expected NxM (e.g. 5x5). Use 'auto' for automatic detection."
        )
    parts = s.split("x", 1)
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError as e:
        raise ValueError(f"Invalid --modules '{s}': must be integers like 5x5. Got: {e}") from e
    if a < 1 or b < 1:
        raise ValueError(f"Invalid --modules '{s}': both dimensions must be >= 1.")
    return a, b


def infer_modules(
    mesh: "trimesh.Trimesh",
    pitch_src: float,
    tol_mm: float = 2.0,
) -> tuple[int, int]:
    """Infer NxM module count from mesh XY footprint. Raises ValueError if footprint does not match."""
    import trimesh

    minx, maxx, miny, maxy = mesh_bounds_xy(mesh)
    w = maxx - minx
    d = maxy - miny

    if w <= 0 or d <= 0:
        raise ValueError(
            f"Module detection failed: mesh has degenerate XY footprint ({w:.2f}x{d:.2f} mm)."
        )

    n = int(round(w / pitch_src))
    m = int(round(d / pitch_src))

    if n < 1 or m < 1:
        raise ValueError(
            f"Module detection failed: inferred {n}x{m}. Use --modules NxM to specify explicitly."
        )

    err_x = abs(w - n * pitch_src)
    err_y = abs(d - m * pitch_src)
    if err_x > tol_mm or err_y > tol_mm:
        raise ValueError(
            f"Module detection failed: footprint {w:.2f}x{d:.2f}mm not close to {n}x{m} at {pitch_src}mm. "
            f"Off by X={err_x:.2f}mm, Y={err_y:.2f}mm. Use --modules NxM to override."
        ) from None

    return n, m


def validate_ref_tile_pitch(
    mesh: "trimesh.Trimesh",
    target_pitch_mm: float,
    tol_mm: float = 1.5,
) -> None:
    """Validate that reference tile XY footprint is close to target_pitch_mm. Raises ValueError if not."""
    minx, maxx, miny, maxy = mesh_bounds_xy(mesh)
    w = maxx - minx
    d = maxy - miny
    err_x = abs(w - target_pitch_mm)
    err_y = abs(d - target_pitch_mm)
    if err_x > tol_mm or err_y > tol_mm:
        raise ValueError(
            f"Reference tile pitch mismatch: tile is {w:.2f}x{d:.2f}mm, target is {target_pitch_mm}mm."
        ) from None
