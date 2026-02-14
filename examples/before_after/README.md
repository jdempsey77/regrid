# Before/after overlay

This folder is for **overlay screenshots** that show the same Gridfinity bin before and after ReGrid conversion (e.g. 42 mm → 21 mm pitch).

## How to create an overlay screenshot

1. **Run a conversion** from the repo root:
   ```bash
   regrid convert samples/sample_42_1x1.stl --export-debug
   ```
   Output goes to `out/` and debug meshes to `debug/` (do not commit those; they are in `.gitignore`).

2. **Open both meshes** in a viewer that supports transparency or two layers (e.g. Blender, MeshLab, or a CAD viewer):
   - Original: `samples/sample_42_1x1.stl`
   - Converted: the file written under `out/` (path printed by the CLI)

3. **Align and style:**
   - Place both at the same origin so they overlap.
   - Give one mesh a semi-transparent material or wireframe so the other shows through.
   - Optionally color the original and converted differently (e.g. before = gray, after = solid).

4. **Export a screenshot** and save it here (e.g. `overlay.png` or `postit_42_to_21.png`). You can commit the image; do not commit generated `debug/*.stl` or `out/*.stl` from the repo root—they remain local and gitignored.
