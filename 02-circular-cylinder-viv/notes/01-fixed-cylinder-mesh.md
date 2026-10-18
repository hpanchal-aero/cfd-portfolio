# 01 — Fixed-cylinder mesh (working note)

Status: meshes generated, converted and checked with checkMesh. No solver run yet.

## Domain and generation
- Units of D (D = 1). x from -15 to 30, y from -15 to 15, thickness 0.1 (one cell in z).
  Blockage D/H = 1/30 = 3.3 %. These extents are my implementation choice and are tested later
  by a domain-size study (not yet done).
- Generator: scripts/meshing/cylinder_mesh.py (Gmsh 4.15.2, OCC). Quad boundary layer on the
  cylinder (design values: first layer 0.005 D, ratio 1.1, total 0.15 D), refined wake box
  (x 0..20, |y| < 2), extruded one layer -> hexahedra.
- Driver: scripts/meshing/mesh_case.sh <level> <case_dir> (Gmsh -> gmshToFoam -> patch types
  -> checkMesh). Patches: inlet, outlet, top, bottom, cylinder (wall), front/back (empty).
- Levels differ by a linear factor 1.4 in cell size (1/1.4, 1, 1.4).

## checkMesh results (-allGeometry -allTopology), all three: Mesh OK, all hexahedra, no prisms
| level  | cells  | cylinder faces | max non-orth | avg non-orth | max aspect | max skewness | total volume |
|--------|--------|----------------|--------------|--------------|------------|--------------|--------------|
| coarse | 14,440 | 88             | 41.37        | 8.41         | 11.33      | 0.630        | 134.922      |
| medium | 28,663 | 122            | 33.26        | 5.93         | 15.38      | 0.803        | 134.921      |
| fine   | 54,558 | 170            | 28.30        | 4.64         | 13.94      | 0.951        | 134.921      |
Expected volume (45*30 - pi/4) * 0.1 = 134.92: matches.

## Skewness outliers (located with checkMesh -meshQuality, limit lowered on purpose)
- medium: 1 face above 0.6, at (12.8, 2.87), edge of the wake refinement box.
- fine: 2 faces above 0.7, at (-1.98, 0.57) (upstream, where near-cylinder refinement hands over)
  and (16.24, -2.55) (wake box edge). The first is the closest to the body; the upstream flow
  is close to potential flow, so I accept it. First thing to revisit if the fine-mesh forces
  look inconsistent with the other levels.
- twoInternalFacesCells (4 cells) are the four domain corners: expected.

## Reproducibility caveat
- Gmsh does not give bit-identical files between runs, even with one thread (md5 differs).
  Cell count and patches are identical; quality values differ at the third digit
  (medium max aspect 15.4693 vs 15.3773 between two runs).
- Gmsh prints "Cannot apply Blossom: odd number of triangles (12321) in surface 1" for the
  medium level: the fallback recombination is used; result is still all-hex.
- The mesh used is therefore recorded by checksum in each case (cases/fixed_Re100_<level>/mesh.md5).
  md5 of the meshes converted into the cases: coarse b3ea0ae6..., medium be32ad72...,
  fine 13707e79...

## Not yet checked
- Near-wall resolution against the actual boundary layer at Re = 100 and 150 (to be judged
  from the solution, not from the design values above).
- Domain-size sensitivity and time-step sensitivity.
