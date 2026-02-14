"""Tiling: replicate reference slab to form NxM grid at target pitch."""

from __future__ import annotations

import trimesh


def tile_reference(
    ref_slice: trimesh.Trimesh,
    nx: int,
    ny: int,
    pitch_dst: float,
) -> trimesh.Trimesh:
    """
    Tile ref_slice nx by ny at pitch_dst spacing.
    Tiles are placed at (i * pitch_dst, j * pitch_dst) for i in [0..nx-1], j in [0..ny-1].
    """
    tiles = []
    for i in range(nx):
        for j in range(ny):
            t = ref_slice.copy()
            t.apply_translation([i * pitch_dst, j * pitch_dst, 0])
            tiles.append(t)
    slab = trimesh.util.concatenate(tiles)
    slab.merge_vertices()
    return slab
