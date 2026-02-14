"""Cut operations: keep mesh above or below a Z plane using boolean intersection."""

from __future__ import annotations

import trimesh

from .boolean import manifold_intersect


def cut_keep_above(mesh: trimesh.Trimesh, z_cut: float) -> trimesh.Trimesh:
    """Keep portion of mesh above z_cut using boolean intersection with a half-space box."""
    b = mesh.bounds
    minx, miny = b[0, 0], b[0, 1]
    maxx, maxy = b[1, 0], b[1, 1]
    maxz = b[1, 2]

    box = trimesh.creation.box(
        extents=[(maxx - minx) + 50, (maxy - miny) + 50, (maxz - z_cut) + 200],
        transform=trimesh.transformations.translation_matrix(
            [(minx + maxx) / 2, (miny + maxy) / 2, (z_cut + maxz) / 2]
        ),
    )
    box.apply_translation([0, 0, (z_cut - box.bounds[0, 2])])

    return manifold_intersect(mesh, box)


def cut_keep_below(mesh: trimesh.Trimesh, z_cut: float) -> trimesh.Trimesh:
    """Keep portion of mesh below z_cut using boolean intersection with a half-space box."""
    b = mesh.bounds
    minx, miny = b[0, 0], b[0, 1]
    maxx, maxy = b[1, 0], b[1, 1]
    minz = b[0, 2]

    box = trimesh.creation.box(
        extents=[(maxx - minx) + 50, (maxy - miny) + 50, (z_cut - minz) + 200],
        transform=trimesh.transformations.translation_matrix(
            [(minx + maxx) / 2, (miny + maxy) / 2, (minz + z_cut) / 2]
        ),
    )
    box.apply_translation([0, 0, (z_cut - box.bounds[1, 2])])

    return manifold_intersect(mesh, box)
