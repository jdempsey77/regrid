"""
CLI entrypoint: subcommands convert and floor.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .detect import detect_floor_z_with_confidence
from .pipeline import PipelineConfig, PITCH_DST_DEFAULT, PITCH_SRC_DEFAULT, run


def _resolve_ref_path() -> Path:
    """Resolve path to reference tile (refs/tile_21_1x1.stl under repo root)."""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]
    return repo_root / "refs" / "tile_21_1x1.stl"


def _run_floor(input_path: str, output_path: str = "debug/floor_plane.stl", verbose: bool = False) -> int:
    """Floor subcommand: detect z_floor, print it and optional confidence; export thin plate."""
    import trimesh

    mesh = trimesh.load_mesh(input_path, force="mesh")
    mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    z_floor, stability = detect_floor_z_with_confidence(mesh)
    if z_floor is None:
        print(
            "Error: Could not detect interior floor plane.\n"
            "The mesh may have no clear horizontal cross-section in the first 15 mm, or the geometry is ambiguous.",
            file=sys.stderr,
        )
        return 1
    print(f"z_floor={z_floor:.3f} mm")
    if verbose:
        print(f"area_stability={stability:.3f} (1.0 = fully stable)")
    b = mesh.bounds
    w = float(b[1, 0] - b[0, 0])
    d = float(b[1, 1] - b[0, 1])
    cx = float((b[0, 0] + b[1, 0]) / 2)
    cy = float((b[0, 1] + b[1, 1]) / 2)
    plate_thickness = 0.2
    plate = trimesh.creation.box(
        extents=[w, d, plate_thickness],
        transform=trimesh.transformations.translation_matrix(
            [cx, cy, z_floor + plate_thickness / 2]
        ),
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plate.export(out.as_posix())
    print(f"Exported {out.resolve()}")
    return 0


def main() -> int:
    """Parse args and dispatch to convert or floor. Returns exit code."""
    ap = argparse.ArgumentParser(
        prog="regrid",
        description="ReGrid — Convert Gridfinity bins between grid pitches. Same bin. New grid.",
    )
    sub = ap.add_subparsers(dest="command", required=True, help="Command")

    # ─── convert ───
    convert_p = sub.add_parser("convert", help="Convert bin to target grid pitch (preserve floor by default)")
    convert_p.add_argument("input", help="Input STL path (42 mm Gridfinity bin)")
    convert_p.add_argument("--out", default=None, help="Output STL path (default: out/<stem>_21mm.stl)")
    convert_p.add_argument(
        "--no-preserve-floor",
        action="store_true",
        help="Use fixed replace-height instead of auto-detected floor",
    )
    convert_p.add_argument(
        "--replace-height-mm",
        type=float,
        default=7.0,
        help="Height of bottom region when not preserving floor (mm); also fallback if floor detection fails",
    )
    convert_p.add_argument(
        "--floor-epsilon-mm",
        type=float,
        default=0.1,
        help="In preserve-floor mode: cut body this far below floor plane to keep coplanar floor faces (mm)",
    )
    convert_p.add_argument(
        "--ref-height-mm",
        type=float,
        default=None,
        help="Height of reference tile slice (default: same as replace-height or effective region)",
    )
    convert_p.add_argument(
        "--floor-cap-mm",
        type=float,
        default=1.6,
        help="Height of flat floor cap when not preserving floor (mm)",
    )
    convert_p.add_argument(
        "--bottom-extension-mm",
        type=float,
        default=0.0,
        help="Extra thickness below original bottom for slab only (mm)",
    )
    convert_p.add_argument(
        "--modules",
        default="auto",
        help="Module count: 'auto' or NxM (e.g. 5x5)",
    )
    convert_p.add_argument(
        "--rotate",
        type=int,
        default=0,
        choices=[0, 90, 180, 270],
        help="Rotate input mesh around Z before processing",
    )
    convert_p.add_argument(
        "--export-debug",
        action="store_true",
        help="Export debug meshes (body_only, slab_only, pre_union) to debug/",
    )
    convert_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip union; only export debug meshes",
    )
    convert_p.add_argument(
        "--verify",
        action="store_true",
        help="After writing output, verify geometry above floor plane matches original (requires pip install \"regrid[verify]\")",
    )
    convert_p.add_argument(
        "--verify-tol-mm",
        type=float,
        default=0.05,
        help="Max nearest-neighbor distance (mm) for --verify; fail if exceeded",
    )
    convert_p.add_argument("--pitch-src", type=float, default=PITCH_SRC_DEFAULT, help="Source grid pitch (mm)")
    convert_p.add_argument("--pitch-dst", type=float, default=PITCH_DST_DEFAULT, help="Target grid pitch (mm)")
    convert_p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # ─── floor ───
    floor_p = sub.add_parser("floor", help="Detect interior floor plane and export debug/floor_plane.stl")
    floor_p.add_argument("input", help="Input STL path")
    floor_p.add_argument("--output", default="debug/floor_plane.stl", help="Output path for floor plane STL")
    floor_p.add_argument("-v", "--verbose", action="store_true", help="Print area stability (confidence)")

    args = ap.parse_args()

    if args.command == "floor":
        return _run_floor(args.input, args.output, getattr(args, "verbose", False))

    # convert
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    ref_path = _resolve_ref_path()
    if not ref_path.exists():
        print(
            f"Error: Missing reference tile: {ref_path}\n"
            "Run from repo root so refs/tile_21_1x1.stl is found.",
            file=sys.stderr,
        )
        return 1

    out_path = Path(args.out) if args.out else Path("out") / (Path(args.input).stem + "_21mm.stl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ref_h = args.ref_height_mm if args.ref_height_mm is not None else args.replace_height_mm

    config = PipelineConfig(
        input_path=args.input,
        out_path=out_path,
        ref_path=ref_path,
        preserve_floor=not args.no_preserve_floor,
        floor_epsilon_mm=args.floor_epsilon_mm,
        replace_height_mm=args.replace_height_mm,
        ref_height_mm=ref_h,
        floor_cap_mm=args.floor_cap_mm,
        bottom_extension_mm=args.bottom_extension_mm,
        modules=args.modules,
        rotate=args.rotate,
        export_debug=args.export_debug,
        dry_run=args.dry_run,
        verify=args.verify,
        verify_tol_mm=args.verify_tol_mm,
        pitch_src=args.pitch_src,
        pitch_dst=args.pitch_dst,
    )

    try:
        run(config)
        return 0
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
