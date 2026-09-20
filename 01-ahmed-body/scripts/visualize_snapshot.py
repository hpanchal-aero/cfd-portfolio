#!/usr/bin/env python3
"""
Single-instant flow-field visualization for the 0deg Ahmed body
transient case, at t=0.45s.

SCOPE, STATED EXPLICITLY: this is a single-timestep snapshot, NOT a
wake-evolution sequence like the 25deg case's 7-frame recirculation-
bubble visualization. Only two near-identical timesteps (t=0.449,
t=0.45, 0.001s apart) exist in the actual oscillation region of this
run -- insufficient to show the wake's temporal evolution. This script
produces contour plots of the flow structure at one instant only.

Reads reconstructed OpenFOAM field data (already reconstructPar'd from
processor*/ into the case root) via PyVista's OpenFOAM reader.

Usage:
    python3 visualize_snapshot.py <case_dir> <time> [--label 00deg]
"""
import argparse
import os
import pyvista as pv
import numpy as np


def load_case(case_dir, time_value):
    foam_file = os.path.join(case_dir, "case.foam")
    if not os.path.exists(foam_file):
        open(foam_file, "w").close()

    reader = pv.POpenFOAMReader(foam_file)
    reader.cell_to_point_creation = True
    reader.set_active_time_value(time_value)
    mesh = reader.read()
    return mesh["internalMesh"]


def make_slice(mesh, y_value=0.10):
    """Longitudinal slice at fixed y (matches the 25deg case's approach:
    a y=0.10m slice through the near-wake, off the symmetry plane)."""
    return mesh.slice(normal=(0, 1, 0), origin=(0, y_value, 0))

def render_contour(slice_mesh, field_name, component, out_path, title,
                    clim=None, cmap="RdBu_r"):
    plotter = pv.Plotter(off_screen=True, window_size=(1600, 900))

    if component is not None:
        data = np.asarray(slice_mesh[field_name][:, component])
        scalars_name = f"{field_name}_{component}"
        slice_mesh[scalars_name] = data
        active = scalars_name
    else:
        data = np.asarray(slice_mesh[field_name])
        active = field_name

    # Diagnostic: print actual data range before rendering, so a
    # degenerate/flat-looking plot can be diagnosed rather than
    # silently trusted.
    print(f"  {active}: min={np.nanmin(data):.4f}, max={np.nanmax(data):.4f}, "
          f"mean={np.nanmean(data):.4f}, std={np.nanstd(data):.4f}")

    if clim is None:
        dmin, dmax = np.nanmin(data), np.nanmax(data)
        drange = dmax - dmin
        dstd = np.nanstd(data)
        if dstd > 0 and drange / dstd > 20:
            print(f"  WARNING: data range ({drange:.2f}) is >20x the std dev "
                  f"({dstd:.2f}) -- likely outlier-dominated. Using percentile "
                  f"clipping (1st-99th) instead of full min/max for the color scale.")
            clim = (np.nanpercentile(data, 1), np.nanpercentile(data, 99))
        else:
            clim = (dmin, dmax)

    plotter.add_mesh(slice_mesh, scalars=active, cmap=cmap, clim=clim,
                      show_scalar_bar=True, scalar_bar_args={"title": title})

    plotter.camera_position = "xz"
    plotter.camera.focal_point = (1.3, 0.10, 0.15)
    plotter.camera.position = (1.3, -1.2, 0.15)
    plotter.camera.zoom(1.8)

    plotter.add_text(title, font_size=14)
    plotter.screenshot(out_path)
    plotter.close()
    print(f"Saved: {out_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("time", type=float)
    parser.add_argument("--label", default="snapshot")
    parser.add_argument("--y-slice", type=float, default=0.10)
    args = parser.parse_args()

    mesh = load_case(args.case_dir, args.time)
    print(f"Loaded mesh at t={args.time}: {mesh.n_cells} cells")

    sl = make_slice(mesh, args.y_slice)

    render_contour(
        sl, "U", component=0,
        out_path=f"{args.label}_Ux_t{args.time}.png",
        title=f"Streamwise velocity Ux (m/s), t={args.time}s, y={args.y_slice}m slice",
        clim=(-25, 25),
    )

    render_contour(
        sl, "p", component=None,
        out_path=f"{args.label}_p_t{args.time}.png",
        title=f"Pressure (kinematic, m^2/s^2), t={args.time}s, y={args.y_slice}m slice",
        cmap="viridis",
    )


if __name__ == "__main__":
    main()
