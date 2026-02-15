#!/usr/bin/env python3
"""
Generate a realistic Gridfinity-style bin with proper floor and walls.

Creates a bin with:
- Solid interior floor at a specific height
- Walls around the perimeter
- Proper dimensions for 42mm pitch

Usage (from repo root):
    python scripts/generate_gridfinity_bin.py

Writes: samples/gridfinity_bin_42mm.stl
"""
from __future__ import annotations

import numpy as np
from pathlib import Path


def create_gridfinity_bin(
    width_mm: float = 42.0,
    depth_mm: float = 42.0,
    total_height_mm: float = 15.0,
    wall_thickness: float = 2.0,
    floor_thickness: float = 2.0,
    base_height: float = 5.0,
) -> "trimesh.Trimesh":
    """
    Create a Gridfinity-style bin with proper interior floor.
    
    Args:
        width_mm: Outer width (X dimension)
        depth_mm: Outer depth (Y dimension)  
        total_height_mm: Total bin height
        wall_thickness: Wall thickness
        floor_thickness: Interior floor thickness
        base_height: Height of the base/interface section
    
    Returns:
        Trimesh representing the bin
    """
    import trimesh
    
    # Interior dimensions
    interior_width = width_mm - (2 * wall_thickness)
    interior_depth = depth_mm - (2 * wall_thickness)
    
    # Create outer shell (full bin)
    outer = trimesh.creation.box(extents=[width_mm, depth_mm, total_height_mm])
    outer.vertices[:, 2] += total_height_mm / 2  # Move to sit on XY plane
    
    # Create interior cavity (to be subtracted)
    cavity_height = total_height_mm - base_height - floor_thickness
    interior = trimesh.creation.box(
        extents=[interior_width, interior_depth, cavity_height]
    )
    # Position cavity: centered in XY, starts above floor
    interior.vertices[:, 2] += base_height + floor_thickness + (cavity_height / 2)
    
    # Boolean difference to create hollow bin with floor
    try:
        bin_mesh = outer.difference(interior, engine='manifold')
    except Exception:
        print("Warning: Boolean operation failed, trying with blender engine...")
        try:
            bin_mesh = outer.difference(interior, engine='blender')
        except Exception:
            print("Warning: All boolean engines failed, returning solid approximation")
            # Fallback: create a simple hollow box manually
            bin_mesh = create_hollow_bin_fallback(
                width_mm, depth_mm, total_height_mm, 
                wall_thickness, floor_thickness, base_height
            )
    
    return bin_mesh


def create_hollow_bin_fallback(
    width: float,
    depth: float,
    height: float,
    wall_thick: float,
    floor_thick: float,
    base_height: float,
) -> "trimesh.Trimesh":
    """Fallback: Create hollow bin by combining primitives."""
    import trimesh
    
    # Floor
    floor = trimesh.creation.box(extents=[width, depth, floor_thick])
    floor.vertices[:, 2] += base_height + floor_thick/2
    
    # Base (solid bottom section)
    base = trimesh.creation.box(extents=[width, depth, base_height])
    base.vertices[:, 2] += base_height / 2
    
    # Walls
    interior_width = width - (2 * wall_thick)
    interior_depth = depth - (2 * wall_thick)
    wall_height = height - base_height - floor_thick
    
    # Front wall
    front = trimesh.creation.box(extents=[width, wall_thick, wall_height])
    front.vertices[:, 1] += (depth - wall_thick) / 2
    front.vertices[:, 2] += base_height + floor_thick + wall_height/2
    
    # Back wall
    back = trimesh.creation.box(extents=[width, wall_thick, wall_height])
    back.vertices[:, 1] -= (depth - wall_thick) / 2
    back.vertices[:, 2] += base_height + floor_thick + wall_height/2
    
    # Left wall
    left = trimesh.creation.box(extents=[wall_thick, interior_depth, wall_height])
    left.vertices[:, 0] -= (width - wall_thick) / 2
    left.vertices[:, 2] += base_height + floor_thick + wall_height/2
    
    # Right wall
    right = trimesh.creation.box(extents=[wall_thick, interior_depth, wall_height])
    right.vertices[:, 0] += (width - wall_thick) / 2
    right.vertices[:, 2] += base_height + floor_thick + wall_height/2
    
    # Combine all parts
    meshes = [base, floor, front, back, left, right]
    combined = trimesh.util.concatenate(meshes)
    
    return combined


def main() -> None:
    try:
        import trimesh
    except ImportError:
        raise SystemExit("trimesh required: pip install trimesh") from None

    repo_root = Path(__file__).resolve().parent.parent
    out_dir = repo_root / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "gridfinity_bin_42mm.stl"

    print("Generating Gridfinity bin with floor and walls...")
    print("  Size: 42×42×15 mm")
    print("  Wall thickness: 2 mm")
    print("  Floor thickness: 2 mm")
    print("  Base height: 5 mm")
    print("  Interior floor at: 7 mm")
    
    bin_mesh = create_gridfinity_bin(
        width_mm=42.0,
        depth_mm=42.0,
        total_height_mm=15.0,
        wall_thickness=2.0,
        floor_thickness=2.0,
        base_height=5.0,
    )
    
    # Ensure manifold and proper normals
    try:
        if hasattr(bin_mesh, 'fill_holes'):
            bin_mesh.fill_holes()
    except Exception as e:
        print(f"  Warning: Could not fill holes: {e}")
    
    try:
        if hasattr(bin_mesh, 'fix_normals'):
            bin_mesh.fix_normals()
    except Exception as e:
        print(f"  Warning: Could not fix normals (scipy may be needed): {e}")
    
    bin_mesh.export(out_path.as_posix())
    
    # Print stats
    print(f"\n✓ Wrote {out_path}")
    print(f"  Vertices: {len(bin_mesh.vertices)}")
    print(f"  Faces: {len(bin_mesh.faces)}")
    print(f"  Bounds (mm):")
    print(f"    X: {bin_mesh.bounds[0][0]:.2f} to {bin_mesh.bounds[1][0]:.2f}")
    print(f"    Y: {bin_mesh.bounds[0][1]:.2f} to {bin_mesh.bounds[1][1]:.2f}")
    print(f"    Z: {bin_mesh.bounds[0][2]:.2f} to {bin_mesh.bounds[1][2]:.2f}")
    print(f"  Is watertight: {bin_mesh.is_watertight}")
    print(f"  Volume: {bin_mesh.volume:.2f} mm³")


if __name__ == "__main__":
    main()
