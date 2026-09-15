#!/usr/bin/env python3
"""
Feature-edge inspection for an Ahmed-body STL, prior to committing to
surfaceFeaturesDict/snappyHexMeshDict feature-angle settings.

Purpose: geometric understanding, NOT final mesh validation. This does
not run snappyHexMesh or OpenFOAM's own surfaceFeatures utility -- it
uses PyVista/VTK's independent feature-edge extraction to sweep a range
of dihedral-angle thresholds and visualize the result, so we can see
whether real sharp edges exist and where, before choosing a value to
hand to OpenFOAM.

Usage:
    python3 inspect_features.py <stl_path> [--label <name>]

Example:
    python3 inspect_features.py geometry/stl/ahmed_body_00deg.stl --label 00deg
"""

import sys
import argparse
import pyvista as pv


# Angle thresholds to sweep. extract_feature_edges(feature_angle=X) flags
# an edge as a "feature" if the dihedral angle between its two adjacent
# faces exceeds X degrees. Sweeping high->low shows how edge count grows
# as the threshold relaxes -- a real sharp corner should show a distinct
# jump somewhere in this range, not a smooth/gradual increase.
ANGLE_SWEEP = [170, 160, 150, 140, 130, 120, 110, 100, 90, 60, 30, 10]


def sweep_feature_angles(mesh):
    print("\nFeature-edge count vs. angle threshold:")
    print(f"{'Threshold (deg)':>16} | {'Edge count':>10}")
    print("-" * 31)
    results = {}
    for angle in ANGLE_SWEEP:
        edges = mesh.extract_feature_edges(
            feature_angle=angle,
            boundary_edges=False,
            non_manifold_edges=False,
            manifold_edges=False,
            feature_edges=True,
        )
        n = edges.n_cells
        results[angle] = n
        print(f"{angle:>16} | {n:>10}")
    return results


def render_views(mesh, label, feature_angle_candidates):
    """Render the body with feature edges highlighted, from a few
    angles chosen to expose the rear/roof junction region specifically
    (where the 25deg trihedral-corner problem lived)."""

    for fa in feature_angle_candidates:
        edges = mesh.extract_feature_edges(
            feature_angle=fa,
            boundary_edges=False,
            non_manifold_edges=False,
            manifold_edges=False,
            feature_edges=True,
        )

        plotter = pv.Plotter(off_screen=True, window_size=(1400, 1000))
        plotter.add_mesh(mesh, color="lightgray", opacity=0.5, show_edges=False)
        if edges.n_cells > 0:
            plotter.add_mesh(edges, color="red", line_width=4)

        # Isometric overview
        plotter.camera_position = "iso"
        plotter.camera.zoom(1.3)
        out_iso = f"feature_inspect_{label}_angle{fa}_iso.png"
        plotter.screenshot(out_iso)
        print(f"Saved: {out_iso}")

        # Rear/roof junction close-up: body spans x in [0,1.044], look
        # from the side (along -y-ish, slightly elevated) focused on the
        # rear-top region where roof meets rear face.
        plotter.camera_position = [
            (2.2, -1.2, 0.9),   # camera location
            (0.95, 0.0, 0.22),  # focal point: rear-top region of body
            (0, 0, 1),          # view-up
        ]
        plotter.camera.zoom(1.0)
        out_rear = f"feature_inspect_{label}_angle{fa}_rear.png"
        plotter.screenshot(out_rear)
        print(f"Saved: {out_rear}")

        plotter.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stl_path")
    parser.add_argument("--label", default="body")
    args = parser.parse_args()

    mesh = pv.read(args.stl_path)
    print(f"Loaded {args.stl_path}: {mesh.n_cells} triangles")

    sweep_feature_angles(mesh)

    # Render at two candidate thresholds under discussion (150, 120)
    # plus a tighter one (90) to see if a real edge is being missed by
    # the candidates, and a looser one (160) to see if 150 is already
    # picking up near-flat noise.
    render_views(mesh, args.label, feature_angle_candidates=[160, 150, 120, 90])


if __name__ == "__main__":
    main()
