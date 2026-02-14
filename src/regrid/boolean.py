"""Boolean operations via manifold3d with clear error handling."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import trimesh

from manifold3d import Manifold, Mesh, OpType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _trimesh_to_manifold_mesh(tm: trimesh.Trimesh) -> Mesh:
    """Convert trimesh to manifold3d.Mesh (float32 vertices, uint32 faces)."""
    verts = np.ascontiguousarray(tm.vertices.astype(np.float32))
    faces = np.ascontiguousarray(tm.faces.astype(np.uint32))
    return Mesh(vert_properties=verts, tri_verts=faces)


def _trimesh_from_manifold(m: Manifold) -> trimesh.Trimesh:
    """Convert Manifold result back to trimesh.Trimesh."""
    mesh = m.to_mesh()
    verts = np.ascontiguousarray(mesh.vert_properties[:, :3].astype(np.float64))
    faces = np.ascontiguousarray(mesh.tri_verts.astype(np.int32))
    out = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    out.remove_unreferenced_vertices()
    return out


def manifold_intersect(a: trimesh.Trimesh, b: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Boolean intersection of two meshes using manifold3d.
    Raises RuntimeError with diagnostics if the operation fails.
    """
    try:
        ma = Manifold(_trimesh_to_manifold_mesh(a))
        mb = Manifold(_trimesh_to_manifold_mesh(b))
        result = Manifold.batch_boolean([ma, mb], OpType.Intersect)
        return _trimesh_from_manifold(result)
    except Exception as e:
        raise RuntimeError(
            f"Boolean intersection failed: {e}. "
            "Check that both meshes are manifold (watertight) and not degenerate. "
            "Try --export-debug to inspect body_only.stl and slab_only.stl."
        ) from e


def manifold_union(a: trimesh.Trimesh, b: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Boolean union of two meshes using manifold3d.
    Raises RuntimeError with diagnostics if the operation fails.
    """
    try:
        ma = Manifold(_trimesh_to_manifold_mesh(a))
        mb = Manifold(_trimesh_to_manifold_mesh(b))
        result = Manifold.batch_boolean([ma, mb], OpType.Add)
        return _trimesh_from_manifold(result)
    except Exception as e:
        raise RuntimeError(
            f"Boolean union failed: {e}. "
            "Check that both meshes are manifold (watertight). "
            "Use --export-debug or --dry-run to inspect body_only.stl and slab_only.stl."
        ) from e
