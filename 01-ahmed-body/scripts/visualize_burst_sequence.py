#!/usr/bin/env python3
"""
Wake-evolution sequence visualization for the 10deg Ahmed body
transient case, spanning one Cd burst cycle identified by
estimate_period_peaks.py (peak at t=0.199-0.210s, flanked by troughs
at approximately t=0.183s and t=0.231s).

UNLIKE the 0deg case (single-instant snapshot only, insufficient
surviving time directories due to purgeWrite 2), this case's
cutPlaneSurface postProcessing function object wrote a y=0.10m slice
at every write time (0.001s interval) regardless of purgeWrite, so a
full burst-cycle sequence is available here.

Reads pre-sliced cutPlane.vtk files directly (already point data:
U, p) -- NOT via POpenFOAMReader/reconstructed time directories like
visualize_snapshot.py uses for the 0deg case. Same slice plane
(y=0.10m), same rendering conventions (percentile-clipping outlier
guard, camera position) reused from that script.

Usage:
    python3 visualize_burst_sequence.py <case_dir> \
        --times 0.18 0.19 0.199 0.205 0.21 0.22 0.231 0.24 \
        --label 10deg_burst1
"""
import argparse
import os
import pyvista as pv
import numpy as np


def load_slice(case_dir, time_value):
    """time_value must match an existing postProcessing/cutPlaneSurface/<t>
    directory name exactly as OpenFOAM wrote it (e.g. '0.199', not
    '0.1990' or '0.19900000')."""
    path = os.path.join(case_dir, "postProcessing", "cutPlaneSurface",
                         time_value, "cutPlane.vtk")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No slice file at {path}")
    return pv.read(path)


def render_contour(slice_mesh, field_name, component, out_path, title,
                    clim=None, cmap="RdBu_r"):
    plotter = pv.Plotter(off_screen=True, window_size=(1600, 900))

    if component is not None:
        data = np.asarray(slice_mesh.point_data[field_name][:, component])
        scalars_name = f"{field_name}_{component}"
        slice_mesh[scalars_name] = data
        active = scalars_name
    else:
        data = np.asarray(slice_mesh.point_data[field_name])
        active = field_name

    print(f"  {active}: min={np.nanmin(data):.4f}, max={np.nanmax(data):.4f}, "
          f"mean={np.nanmean(data):.4f}, std={np.nanstd(data):.4f}")

    # Wake-region-only diagnostic (x>0.9m) -- the whole-slice stats
    # above are dominated by the front-nose fillet (verified: p there
    # reaches -2765/+1484, ~10x the wake's range) and do not show
    # whether frames differ where it matters for this sequence.
    if "x" not in dir():
        pass
    x_coords = slice_mesh.points[:, 0]
    wake_mask = x_coords > 0.9
    wake_data = data[wake_mask] if len(data) == len(wake_mask) else None
    if wake_data is not None and len(wake_data) > 0:
        print(f"  {active} (wake x>0.9, n={wake_mask.sum()}): "
              f"min={np.nanmin(wake_data):.4f}, max={np.nanmax(wake_data):.4f}, "
              f"mean={np.nanmean(wake_data):.4f}, std={np.nanstd(wake_data):.4f}")

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

    # Same camera convention as visualize_snapshot.py (0deg case).
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
    parser.add_argument("--times", nargs="+", required=True,
                         help="Time values matching cutPlaneSurface/<t> "
                              "directory names exactly (e.g. 0.199).")
    parser.add_argument("--label", default="burst")
    parser.add_argument("--out-dir", default=".")
    # SAME clim for Ux across all frames in a sequence, so frames are
    # visually comparable (per project convention: consistent contour
    # limits across compared cases/frames unless explicitly justified).
    parser.add_argument("--ux-clim", type=float, nargs=2, default=[-30, 90])
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # First pass: load all frames to determine a SHARED pressure clim.
    # Restricted to the WAKE region (x > 0.9m) -- the front-nose fillet
    # (x < 0.1m) produces pressure extremes an order of magnitude
    # larger than anything in the wake (verified: -2765 to +1484 at the
    # nose vs a much narrower range in the wake), which would otherwise
    # dominate the color scale and hide the wake structure this
    # sequence is meant to show.
    slices = {}
    all_p_wake = []
    for t in args.times:
        sl = load_slice(args.case_dir, t)
        slices[t] = sl
        p = np.asarray(sl.point_data["p"])
        x = sl.points[:, 0]
        all_p_wake.append(p[x > 0.9])
    all_p_wake = np.concatenate(all_p_wake)
    p_lo, p_hi = np.nanpercentile(all_p_wake, [1, 99])
    print(f"Shared WAKE-REGION (x>0.9m) pressure clim across "
          f"{len(args.times)} frames (1st-99th pct): ({p_lo:.2f}, {p_hi:.2f})")

    for t in args.times:
        print(f"\n=== t={t} ===")
        sl = slices[t]
        render_contour(
            sl, "U", component=0,
            out_path=os.path.join(args.out_dir, f"{args.label}_Ux_t{t}.png"),
            title=f"Streamwise velocity Ux (m/s), t={t}s, y=0.10m slice",
            clim=tuple(args.ux_clim),
        )
        render_contour(
            sl, "p", component=None,
            out_path=os.path.join(args.out_dir, f"{args.label}_p_t{t}.png"),
            title=f"Pressure (kinematic, m^2/s^2), t={t}s, y=0.10m slice",
            clim=(p_lo, p_hi),
            cmap="viridis",
        )


if __name__ == "__main__":
    main()
