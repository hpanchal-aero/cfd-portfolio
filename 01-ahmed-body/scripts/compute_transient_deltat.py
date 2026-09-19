#!/usr/bin/env python3
"""
Compute the required initial deltaT for a transient PIMPLE run, from the
ACTUAL generated mesh's finest cell size (read via PyVista's OpenFOAM
reader), targeting a specified Courant number and characteristic
velocity. This is a post-meshing calculation -- it requires the mesh to
already exist, unlike compute_yplus_layer.py which is a pre-meshing
sizing estimate.

Co = U * deltaT / dx  =>  deltaT = Co_target * dx_min / U_characteristic

dx_min is estimated two ways for cross-checking:
  1. Volume-based: dx_min = (min_cell_volume)^(1/3)  -- a proxy, biased
     if the smallest-volume cell is very anisotropic (thin in one
     direction, larger in others).
  2. Direct extent-based: for the N smallest-volume cells, compute the
     actual bounding-box extent in each direction and report the
     smallest such extent found -- more representative of what
     actually limits an explicit/semi-implicit timestep in the flow
     direction.

Usage:
    python3 compute_transient_deltat.py <case_dir> --U 60 --co-target 0.5

Example:
    python3 compute_transient_deltat.py \
        ~/cfd-portfolio/01-ahmed-body/cases/slant00_re4.18M_symtest_transient \
        --U 60 --co-target 0.5
"""

import argparse
import os
import numpy as np
import pyvista as pv


def load_mesh(case_dir):
    foam_file = os.path.join(case_dir, "case.foam")
    if not os.path.exists(foam_file):
        open(foam_file, "w").close()

    reader = pv.POpenFOAMReader(foam_file)
    reader.cell_to_point_creation = False
    mesh = reader.read()

    internal = mesh["internalMesh"]
    return internal


def analyze_cell_sizes(mesh, n_smallest=50):
    volumes = mesh.compute_cell_sizes(length=False, area=False, volume=True)["Volume"]

    dx_volume_based = np.cbrt(volumes.min())

    n = min(n_smallest, len(volumes))
    smallest_indices = np.argsort(volumes)[:n]

    min_extent = np.inf
    for idx in smallest_indices:
        cell = mesh.extract_cells([idx])
        bounds = cell.bounds
        extents = [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]]
        min_extent = min(min_extent, min(e for e in extents if e > 0))

    return {
        "min_volume_m3": float(volumes.min()),
        "dx_volume_based_m": float(dx_volume_based),
        "dx_extent_based_m": float(min_extent),
        "n_cells_checked_for_extent": n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--U", type=float, required=True,
                         help="Characteristic velocity for Courant number [m/s].")
    parser.add_argument("--co-target", type=float, default=0.5)
    parser.add_argument("--n-smallest", type=int, default=50)
    args = parser.parse_args()

    mesh = load_mesh(args.case_dir)
    print(f"Internal mesh: {mesh.n_cells} cells")

    sizes = analyze_cell_sizes(mesh, args.n_smallest)

    print(f"\nMin cell volume: {sizes['min_volume_m3']:.6e} m^3")
    print(f"dx (volume-based, cube root): {sizes['dx_volume_based_m']*1000:.6f} mm")
    print(f"dx (direct extent, smallest of {sizes['n_cells_checked_for_extent']} "
          f"smallest-volume cells): {sizes['dx_extent_based_m']*1000:.6f} mm")

    if sizes["dx_extent_based_m"] < sizes["dx_volume_based_m"] * 0.5:
        print("\nNOTE: direct extent is less than half the volume-based estimate -- "
              "smallest cells are significantly anisotropic. Using the smaller "
              "(more conservative) extent-based value for deltaT.")

    dx_for_deltat = min(sizes["dx_volume_based_m"], sizes["dx_extent_based_m"])

    deltaT = args.co_target * dx_for_deltat / args.U

    print(f"\n--- deltaT recommendation ---")
    print(f"Using dx = {dx_for_deltat*1000:.6f} mm, U = {args.U} m/s, "
          f"target Co = {args.co_target}")
    print(f"Recommended initial deltaT = {deltaT:.6e} s")
    print(f"(adjustTimeStep will self-correct from this starting point)")


if __name__ == "__main__":
    main()
