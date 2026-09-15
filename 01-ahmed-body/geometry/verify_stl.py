#!/usr/bin/env python3
"""
Verify an Ahmed-body STL file before it is used for meshing.

Checks:
  1. File loads without error (valid STL, binary or ASCII)
  2. Triangle count
  3. Bounding box (expect meter-scale: x in [0, ~1.044], y in [0, ~0.389]
     or [0, ~0.1945] for a half-body, z in [0, ~0.288+ground clearance])
  4. Volume (mesh.volume, only meaningful if closed/manifold)
  5. Watertight / manifold check (open edge count)

Usage:
    python3 verify_stl.py <stl_path> [--compare <reference_stl_path>]

Example:
    python3 verify_stl.py geometry/stl/ahmed_body_00deg.stl \
        --compare geometry/stl/ahmed_body_25deg.stl
"""

import sys
import argparse
import pyvista as pv
import numpy as np


def inspect(path):
    mesh = pv.read(path)

    n_tris = mesh.n_cells
    bounds = mesh.bounds  # (xmin,xmax,ymin,ymax,zmin,zmax)

    # Open-edge count: edges belonging to only one triangle indicate
    # a non-watertight / non-manifold surface. PyVista's
    # extract_feature_edges(boundary_edges=True, non_manifold_edges=True,
    # feature_edges=False, manifold_edges=False) isolates exactly these.
    edges = mesh.extract_feature_edges(
        boundary_edges=True,
        non_manifold_edges=True,
        feature_edges=False,
        manifold_edges=False,
    )
    n_open_edges = edges.n_cells

    volume = None
    if n_open_edges == 0:
        try:
            volume = mesh.volume
        except Exception as e:
            volume = f"ERROR computing volume: {e}"
    else:
        volume = "SKIPPED (surface not closed -- see open edge count below)"

    return {
        "path": path,
        "n_triangles": n_tris,
        "bounds": bounds,
        "open_edges": n_open_edges,
        "volume_m3": volume,
    }


def report(info):
    print(f"\n=== {info['path']} ===")
    print(f"Triangles       : {info['n_triangles']}")
    xmin, xmax, ymin, ymax, zmin, zmax = info["bounds"]
    print(f"Bounds x        : [{xmin:.6f}, {xmax:.6f}]  (extent {xmax - xmin:.6f} m)")
    print(f"Bounds y        : [{ymin:.6f}, {ymax:.6f}]  (extent {ymax - ymin:.6f} m)")
    print(f"Bounds z        : [{zmin:.6f}, {zmax:.6f}]  (extent {zmax - zmin:.6f} m)")
    print(f"Open edges      : {info['open_edges']} "
          f"({'WATERTIGHT' if info['open_edges'] == 0 else 'NOT WATERTIGHT'})")
    if isinstance(info["volume_m3"], float):
        print(f"Volume          : {info['volume_m3']:.8f} m^3 "
              f"({info['volume_m3'] * 1000:.4f} L)")
    else:
        print(f"Volume          : {info['volume_m3']}")

    # Unit sanity flag: Ahmed body characteristic length L=1.044 m.
    # If bounds are ~1044 instead of ~1.044, geometry is very likely in mm.
    max_extent = max(xmax - xmin, ymax - ymin, zmax - zmin)
    if max_extent > 50:
        print("WARNING: largest bounding-box extent exceeds 50 -- "
              "this looks like millimeter-scale data, not meter-scale.")
    elif max_extent < 0.01:
        print("WARNING: largest bounding-box extent is under 1 cm -- "
              "unexpectedly small for an Ahmed body at any reasonable scale.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stl_path")
    parser.add_argument("--compare", default=None,
                         help="Optional reference STL to compare against")
    args = parser.parse_args()

    target = inspect(args.stl_path)
    report(target)

    if args.compare:
        ref = inspect(args.compare)
        report(ref)

        print(f"\n=== Comparison: {args.stl_path} vs {args.compare} ===")
        tri_diff = target["n_triangles"] - ref["n_triangles"]
        print(f"Triangle count difference : {tri_diff} "
              f"({args.stl_path}={target['n_triangles']}, "
              f"{args.compare}={ref['n_triangles']})")

        for axis, idx in (("x", 0), ("y", 2), ("z", 4)):
            t_min, t_max = target["bounds"][idx], target["bounds"][idx + 1]
            r_min, r_max = ref["bounds"][idx], ref["bounds"][idx + 1]
            print(f"{axis}-extent: target={t_max - t_min:.6f} m, "
                  f"ref={r_max - r_min:.6f} m")

        if isinstance(target["volume_m3"], float) and isinstance(ref["volume_m3"], float):
            print(f"Volume: target={target['volume_m3']*1000:.4f} L, "
                  f"ref={ref['volume_m3']*1000:.4f} L")
            if target["volume_m3"] <= ref["volume_m3"]:
                print("NOTE: target volume <= reference (25deg) volume. "
                      "Expected: 0deg volume should be LARGER than 25deg "
                      "(less material removed by a shallower slant cut). "
                      "If target is 0deg and this inequality does not hold, "
                      "investigate before proceeding.")


if __name__ == "__main__":
    main()
