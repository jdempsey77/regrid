"""
Verify that output mesh is identical to original above the join plane (z_join).
Uses surface sampling and trimesh.proximity (nearest-neighbor distances).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import trimesh

from .cut import cut_keep_above

logger = logging.getLogger(__name__)

VERIFY_SAMPLE_COUNT = 10_000


def verify_above_plane(
    orig_mesh: trimesh.Trimesh,
    out_path: str | bytes,
    z_join: float,
    tol_mm: float,
    sample_count: int = VERIFY_SAMPLE_COUNT,
) -> dict[str, Any]:
    """
    Verify that the mesh at out_path matches orig_mesh above z_join.
    Samples points on both surfaces, computes nearest-neighbor distances both ways.
    Fails (raises RuntimeError) if max distance > tol_mm.

    Returns dict with max_mm, p95 (both directions), passed.
    """
    out_mesh = trimesh.load_mesh(out_path, force="mesh")
    out_mesh = trimesh.Trimesh(
        vertices=out_mesh.vertices,
        faces=out_mesh.faces,
        process=False,
    )

    orig_above = cut_keep_above(orig_mesh, z_join)
    out_above = cut_keep_above(out_mesh, z_join)

    def sample_and_distances(from_mesh: trimesh.Trimesh, to_mesh: trimesh.Trimesh) -> np.ndarray:
        n = min(sample_count, len(from_mesh.faces))
        if n < 3:
            return np.array([])
        pts, _ = trimesh.sample.sample_surface(from_mesh, n)
        if len(pts) == 0:
            return np.array([])
        _, distance, _ = to_mesh.nearest.on_surface(pts)
        return np.asarray(distance, dtype=np.float64)

    try:
        d_orig_to_out = sample_and_distances(orig_above, out_above)
        d_out_to_orig = sample_and_distances(out_above, orig_above)
    except Exception as e:
        raise RuntimeError(
            f"Verify failed during sampling/proximity. Install extras: pip install \"regrid[verify]\" — {e}"
        ) from e

    max_orig_to_out = float(np.max(d_orig_to_out)) if len(d_orig_to_out) else 0.0
    max_out_to_orig = float(np.max(d_out_to_orig)) if len(d_out_to_orig) else 0.0
    max_mm = max(max_orig_to_out, max_out_to_orig)

    p95_orig_to_out = float(np.percentile(d_orig_to_out, 95)) if len(d_orig_to_out) else 0.0
    p95_out_to_orig = float(np.percentile(d_out_to_orig, 95)) if len(d_out_to_orig) else 0.0

    passed = max_mm <= tol_mm
    stats = {
        "max_mm": max_mm,
        "p95_orig_to_out_mm": p95_orig_to_out,
        "p95_out_to_orig_mm": p95_out_to_orig,
        "passed": passed,
        "tol_mm": tol_mm,
    }

    logger.info(
        "Verify (above z_join=%.3f mm): orig→out max=%.4f mm p95=%.4f mm  out→orig max=%.4f mm p95=%.4f mm  tol=%.2f mm",
        z_join, max_orig_to_out, p95_orig_to_out, max_out_to_orig, p95_out_to_orig, tol_mm,
    )
    if passed:
        logger.info("Verify: PASS (output identical to original above floor plane)")
    else:
        logger.error("Verify: FAIL (max distance %.4f mm > tol %.2f mm)", max_mm, tol_mm)
        raise RuntimeError(
            f"Verify failed: max distance {max_mm:.4f} mm > tolerance {tol_mm} mm."
        )

    return stats
