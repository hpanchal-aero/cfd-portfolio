#!/usr/bin/env python3
"""cylinder_mesh.py -- 2D (one cell thick) mesh of a circular cylinder in a channel-like
domain, written for OpenFOAM (Gmsh MSH 2.2, converted with gmshToFoam).

Everything is in units of the cylinder diameter D (D = 1). The mesh is all-quad near
the cylinder (boundary layer) and recombined elsewhere, then extruded one cell in z,
so the 3D cells are hexahedra (and a few prisms if recombination leaves triangles).

Usage:
    /usr/bin/python3 cylinder_mesh.py --level medium --out cylinder_medium.msh
Run with /usr/bin/python3 (the miniconda python on PATH has no gmsh module).
"""
import argparse
import sys

import gmsh

LEVELS = {"coarse": 1.0 / 1.4, "medium": 1.0, "fine": 1.4}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--level", choices=LEVELS, default="medium",
                    help="resolution level; linear refinement factor 1/1.4, 1, 1.4")
    ap.add_argument("--x-in", type=float, default=15.0, help="inlet distance upstream [D]")
    ap.add_argument("--x-out", type=float, default=30.0, help="outlet distance downstream [D]")
    ap.add_argument("--y-half", type=float, default=15.0, help="half-height of the domain [D]")
    ap.add_argument("--thickness", type=float, default=0.1, help="extrusion thickness [D]")
    ap.add_argument("--out", default="cylinder.msh", help="output file (MSH 2.2 ASCII)")
    args = ap.parse_args()

    s = LEVELS[args.level]
    R = 0.5
    h_wall_t = 0.026 / s       # cell size along the cylinder surface
    h_wall_n = 0.005 / s       # first-layer thickness
    bl_ratio = 1.10
    bl_thick = 0.15            # total boundary-layer thickness [D]
    h_near = 0.060 / s         # size at the end of the near-wall transition
    h_wake = 0.070 / s         # size in the wake box
    h_far = 1.20 / s           # size at the outer boundary

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("cylinder")
    occ = gmsh.model.occ

    rect = occ.addRectangle(-args.x_in, -args.y_half, 0.0,
                            args.x_in + args.x_out, 2 * args.y_half)
    disk = occ.addDisk(0.0, 0.0, 0.0, R, R)
    surf, _ = occ.cut([(2, rect)], [(2, disk)])
    occ.synchronize()
    surf_tag = surf[0][1]

    # curve on the cylinder: the one whose bounding box lies inside radius R
    cyl_curves = []
    for dim, tag in gmsh.model.getEntities(1):
        bb = gmsh.model.getBoundingBox(dim, tag)
        if max(abs(bb[0]), abs(bb[3]), abs(bb[1]), abs(bb[4])) <= R + 1e-6:
            cyl_curves.append(tag)
    if not cyl_curves:
        sys.exit("ERROR: no cylinder curve found")

    fld = gmsh.model.mesh.field
    # distance from the cylinder, size grows from h_wall_t to h_near, then to h_far
    f_dist = fld.add("Distance")
    fld.setNumbers(f_dist, "CurvesList", cyl_curves)
    fld.setNumber(f_dist, "Sampling", 200)
    f_thr = fld.add("Threshold")
    fld.setNumber(f_thr, "InField", f_dist)
    fld.setNumber(f_thr, "SizeMin", h_wall_t)
    fld.setNumber(f_thr, "SizeMax", h_far)
    fld.setNumber(f_thr, "DistMin", 0.3)
    fld.setNumber(f_thr, "DistMax", 14.0)
    # near-field plateau so the cylinder neighbourhood stays fine
    f_near = fld.add("Ball")
    fld.setNumber(f_near, "Radius", 2.0)
    fld.setNumber(f_near, "Thickness", 2.0)
    fld.setNumber(f_near, "VIn", h_near)
    fld.setNumber(f_near, "VOut", h_far)
    fld.setNumber(f_near, "XCenter", 0.0)
    fld.setNumber(f_near, "YCenter", 0.0)
    fld.setNumber(f_near, "ZCenter", 0.0)
    # wake box
    f_wake = fld.add("Box")
    fld.setNumber(f_wake, "VIn", h_wake)
    fld.setNumber(f_wake, "VOut", h_far)
    fld.setNumber(f_wake, "XMin", 0.0)
    fld.setNumber(f_wake, "XMax", 20.0)
    fld.setNumber(f_wake, "YMin", -2.0)
    fld.setNumber(f_wake, "YMax", 2.0)
    fld.setNumber(f_wake, "ZMin", -1.0)
    fld.setNumber(f_wake, "ZMax", 1.0)
    fld.setNumber(f_wake, "Thickness", 4.0)
    f_min = fld.add("Min")
    fld.setNumbers(f_min, "FieldsList", [f_thr, f_near, f_wake])
    fld.setAsBackgroundMesh(f_min)

    # boundary layer of quads on the cylinder
    f_bl = fld.add("BoundaryLayer")
    fld.setNumbers(f_bl, "CurvesList", cyl_curves)
    fld.setNumber(f_bl, "Size", h_wall_n)
    fld.setNumber(f_bl, "Ratio", bl_ratio)
    fld.setNumber(f_bl, "Thickness", bl_thick)
    fld.setNumber(f_bl, "Quads", 1)
    fld.setAsBoundaryLayer(f_bl)

    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 8)               # Frontal-Delaunay for quads
    gmsh.option.setNumber("Mesh.RecombineAll", 1)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 3)  # blossom full-quad
    gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 0)

    # extrude one layer in z: the quads become hexahedra, any triangles prisms
    occ.extrude([(2, surf_tag)], 0, 0, args.thickness, [1], [], True)
    occ.synchronize()

    # --- physical groups, classified by geometry -----------------------------
    L = args.thickness
    tol = 1e-6
    groups = {"inlet": [], "outlet": [], "top": [], "bottom": [],
              "cylinder": [], "back": [], "front": []}
    for dim, tag in gmsh.model.getEntities(2):
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(dim, tag)
        if abs(zmax - zmin) < tol:
            groups["back" if abs(zmin) < tol else "front"].append(tag)
        elif abs(xmin + args.x_in) < tol and abs(xmax + args.x_in) < tol:
            groups["inlet"].append(tag)
        elif abs(xmin - args.x_out) < tol and abs(xmax - args.x_out) < tol:
            groups["outlet"].append(tag)
        elif abs(ymin + args.y_half) < tol and abs(ymax + args.y_half) < tol:
            groups["bottom"].append(tag)
        elif abs(ymin - args.y_half) < tol and abs(ymax - args.y_half) < tol:
            groups["top"].append(tag)
        else:
            groups["cylinder"].append(tag)
    for name, tags in groups.items():
        if not tags:
            sys.exit(f"ERROR: empty physical group {name}")
    vols = [t for d, t in gmsh.model.getEntities(3)]
    for i, (name, tags) in enumerate(groups.items(), start=1):
        gmsh.model.addPhysicalGroup(2, tags, i, name)
    gmsh.model.addPhysicalGroup(3, vols, 100, "fluid")

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.Binary", 0)
    gmsh.option.setNumber("Mesh.SaveAll", 0)
    gmsh.model.mesh.generate(3)
    gmsh.write(args.out)

    # --- report -----------------------------------------------------------------
    etypes, etags, _ = gmsh.model.mesh.getElements(3)
    names = {5: "hexahedra", 6: "prisms", 4: "tetrahedra", 7: "pyramids"}
    print(f"level {args.level}: scale {s:.4f}, thickness {L}")
    for t, tg in zip(etypes, etags):
        print(f"  {names.get(t, t)}: {len(tg)}")
    q = gmsh.model.mesh.getElementQualities(
        [e for tg in etags for e in tg], "minSICN")
    print(f"  min SICN {min(q):.3f}  mean SICN {sum(q)/len(q):.3f}")
    for name, tags in groups.items():
        n = 0
        for t in tags:
            _, et, _ = gmsh.model.mesh.getElements(2, t)
            n += sum(len(e) for e in et)
        print(f"  patch {name}: {n} faces")
    print(f"wrote {args.out}")
    gmsh.finalize()


if __name__ == "__main__":
    main()
