"""
Main orchestration: load mesh, detect modules, cut, tile, align, and union.
Preserve-floor by default: geometry above interior floor plane is unchanged.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
import trimesh

from .boolean import manifold_intersect, manifold_union
from .cut import cut_keep_above, cut_keep_below
from .detect import (
    detect_floor_z,
    infer_modules,
    mesh_center_xy,
    mesh_min_z,
    parse_modules,
    validate_ref_tile_pitch,
)
from .tile import tile_reference
from .verify import verify_above_plane

logger = logging.getLogger(__name__)

PITCH_SRC_DEFAULT = 42.0
PITCH_DST_DEFAULT = 21.0


class PipelineConfig(NamedTuple):
    """Configuration for the convert pipeline."""

    input_path: str
    out_path: Path
    ref_path: Path
    preserve_floor: bool
    floor_epsilon_mm: float
    replace_height_mm: float
    ref_height_mm: float
    floor_cap_mm: float
    bottom_extension_mm: float
    modules: str
    rotate: int
    export_debug: bool
    dry_run: bool
    verify: bool
    verify_tol_mm: float
    pitch_src: float
    pitch_dst: float


def rotate_z(mesh: trimesh.Trimesh, deg: int) -> trimesh.Trimesh:
    """Rotate mesh around Z axis by deg (0, 90, 180, 270)."""
    if deg % 360 == 0:
        return mesh
    radians = np.deg2rad(deg)
    T = trimesh.transformations.rotation_matrix(radians, [0, 0, 1])
    m = mesh.copy()
    m.apply_transform(T)
    return m


def _log_run_summary(
    zmin: float,
    z_join: float,
    z_cut_body: float,
    effective_replace_height: float,
    footprint_preserved: bool,
) -> None:
    """Log a clear end-of-run summary."""
    logger.info("")
    logger.info("Run summary:")
    logger.info("  zmin                    %.3f mm", zmin)
    logger.info("  z_join (floor plane)    %.3f mm", z_join)
    logger.info("  z_cut_body              %.3f mm", z_cut_body)
    logger.info("  effective_replace_height %.3f mm", effective_replace_height)
    logger.info("  footprint preserved     %s", footprint_preserved)


def run(config: PipelineConfig) -> None:
    """
    Run the convert pipeline: load, cut, tile, align, union.
    If dry_run, skip union and only export debug meshes.
    Preserve-floor (default): body is cut below floor plane so interior geometry is kept.
    """
    mesh = trimesh.load_mesh(config.input_path, force="mesh")
    mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    mesh = rotate_z(mesh, config.rotate)

    if config.modules != "auto":
        n, m = parse_modules(config.modules)
        logger.info("Using modules: %dx%d", n, m)
    else:
        n, m = infer_modules(mesh, config.pitch_src)
        logger.info("Inferred modules: %dx%d @ %.1f mm pitch", n, m, config.pitch_src)

    n2 = int(round(n * (config.pitch_src / config.pitch_dst)))
    m2 = int(round(m * (config.pitch_src / config.pitch_dst)))
    logger.info("Target modules: %dx%d @ %.1f mm pitch", n2, m2, config.pitch_dst)

    zmin = mesh_min_z(mesh)
    if config.preserve_floor:
        z_floor = detect_floor_z(mesh)
        if z_floor is not None:
            z_join = z_floor
            z_cut_body = z_join - config.floor_epsilon_mm
            logger.info(
                "Detected interior floor at z_floor=%.3f mm (join plane); cutting body above z_cut_body=%.3f mm",
                z_join, z_cut_body,
            )
        else:
            z_cut = zmin + config.replace_height_mm
            z_join = z_cut
            z_cut_body = z_cut
            logger.warning(
                "Floor detection failed; using replace_height_mm=%.2f (z_cut=%.3f). Use --no-preserve-floor to silence.",
                config.replace_height_mm, z_cut,
            )
    else:
        z_cut = zmin + config.replace_height_mm
        z_join = z_cut
        z_cut_body = z_cut

    body = cut_keep_above(mesh, z_cut_body)

    body_min_x, body_max_x = body.bounds[0, 0], body.bounds[1, 0]
    body_min_y, body_max_y = body.bounds[0, 1], body.bounds[1, 1]
    body_w = body_max_x - body_min_x
    body_d = body_max_y - body_min_y

    ref = trimesh.load_mesh(config.ref_path.as_posix(), force="mesh")
    ref = trimesh.Trimesh(vertices=ref.vertices, faces=ref.faces, process=False)
    validate_ref_tile_pitch(ref, config.pitch_dst)

    effective_replace_height = z_join - zmin
    ref_height_mm = config.ref_height_mm
    if ref_height_mm > effective_replace_height:
        ref_height_mm = effective_replace_height
        logger.warning("ref_height_mm clamped to %.2f mm", ref_height_mm)

    ref_zmin = mesh_min_z(ref)
    ref_slice = cut_keep_below(ref, ref_zmin + ref_height_mm)

    slab = tile_reference(ref_slice, n2, m2, config.pitch_dst)

    body_c = mesh_center_xy(body)
    slab_c = mesh_center_xy(slab)
    slab.apply_translation([body_c[0] - slab_c[0], body_c[1] - slab_c[1], 0])

    overlap = 0.2
    slab_top = slab.bounds[1, 2]
    slab.apply_translation([0, 0, (z_join - slab_top) - overlap])

    if config.bottom_extension_mm != 0:
        slab.apply_translation([0, 0, -config.bottom_extension_mm])

    if not config.preserve_floor:
        cap_top = z_join - overlap
        cap_height = max(config.floor_cap_mm, config.bottom_extension_mm)
        cap_bottom = cap_top - cap_height
        cap_extents = [body_w, body_d, cap_height]
        cap_center_z = (cap_top + cap_bottom) / 2.0
        cap = trimesh.creation.box(
            extents=cap_extents,
            transform=trimesh.transformations.translation_matrix(
                [body_c[0], body_c[1], cap_center_z]
            ),
        )
        slab = manifold_union(slab, cap)

    crop_height = effective_replace_height + config.bottom_extension_mm + 5.0
    crop_center_z = (zmin - config.bottom_extension_mm + z_join) / 2.0
    crop_box = trimesh.creation.box(
        extents=[body_w, body_d, crop_height],
        transform=trimesh.transformations.translation_matrix(
            [body_c[0], body_c[1], crop_center_z]
        ),
    )
    slab = manifold_intersect(slab, crop_box)

    footprint_preserved = True  # slab cropped to body footprint

    export_debug = config.export_debug or config.dry_run
    if export_debug:
        debug_dir = Path("debug").resolve()
        debug_dir.mkdir(exist_ok=True)
        body.export((debug_dir / "body_only.stl").as_posix())
        slab.export((debug_dir / "slab_only.stl").as_posix())
        pre = trimesh.util.concatenate([body.copy(), slab.copy()])
        pre.export((debug_dir / "pre_union.stl").as_posix())
        logger.info("Exported debug meshes to %s/", debug_dir)

    if config.dry_run:
        _log_run_summary(zmin, z_join, z_cut_body, effective_replace_height, footprint_preserved)
        logger.info("Dry run: skipped union. Inspect debug/body_only.stl, slab_only.stl, pre_union.stl")
        return

    result = manifold_union(body, slab)
    result.export(config.out_path.as_posix())
    logger.info("Wrote: %s  (%dx%d @ %.1f mm => %dx%d @ %.1f mm)",
                config.out_path, n, m, config.pitch_src, n2, m2, config.pitch_dst)

    if config.verify:
        verify_above_plane(
            mesh,
            config.out_path.as_posix(),
            z_join,
            config.verify_tol_mm,
        )

    _log_run_summary(zmin, z_join, z_cut_body, effective_replace_height, footprint_preserved)
