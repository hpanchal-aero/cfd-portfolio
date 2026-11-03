#!/usr/bin/env python3
"""flow_snapshots.py -- pressure, velocity-magnitude and vorticity pictures of one moving-cylinder case.

Usage (user packages are needed, so no -I):
    /usr/bin/python3 -E -P scripts/viz/flow_snapshots.py <case_dir> <label> <t_from> <t_to> [<out_root>]

  <case_dir>  OpenFOAM case with saved time directories
  <label>     name of the output folder, e.g. Ur7.75
  <t_from>, <t_to>   choose among the saved times in this range the one where the cylinder centre
                     is at its highest y (same phase for every case, up to the saved-time spacing)
  <out_root>  default results/figures

Same view and colour limits for every case (see FIELDS): window x = -6 .. 15, y = -6 .. 6 (D = 1).
Pressure is the kinematic pressure p/rho of the solver; with U = 1 the picture shows p/(rho U^2) = Cp/2.
Lighting is off, so the colours are exactly those of the colour bar.
Creates an empty <case_dir>/case.foam if missing (ignored by git).
"""
import os
import sys

import numpy as np
import pyvista as pv

pv.OFF_SCREEN = True

XC, YC, HALF_HEIGHT = 4.5, 0.0, 6.0
SIZE = (1400, 800)
FIELDS = {
    "pressure": dict(key="p", cmap="RdBu_r", clim=(-1.3, 1.3), caption="pressure p/(rho U^2)"),
    "velocity": dict(key="|U|", cmap="viridis", clim=(0.0, 1.7), caption="speed (velocity magnitude) U/U_inf"),
    "vorticity": dict(key="wz", cmap="RdBu_r", clim=(-3.5, 3.5), caption="spanwise vorticity w_z D/U_inf"),
}


def read_time(reader, t):
    reader.set_active_time_value(t)
    m = reader.read()
    g = m["internalMesh"]
    b = m["boundary"]["cylinder"].bounds
    return g, 0.5 * (b[0] + b[1]), 0.5 * (b[2] + b[3])


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    case, label = sys.argv[1], sys.argv[2]
    t0, t1 = float(sys.argv[3]), float(sys.argv[4])
    out_root = sys.argv[5] if len(sys.argv) > 5 else "results/figures"

    foam = os.path.join(case, "case.foam")
    if not os.path.exists(foam):
        open(foam, "w").close()
    r = pv.OpenFOAMReader(foam)
    r.enable_all_cell_arrays()
    r.enable_all_point_arrays()
    r.enable_all_patch_arrays()

    times = [t for t in r.time_values if t0 <= t <= t1 and t > 0]
    if not times:
        sys.exit("no saved time in [%g, %g]; saved: %s" % (t0, t1, list(r.time_values)))
    cys = []
    for t in times:
        _, cx, cy = read_time(r, t)
        cys.append(cy)
        print("  t = %7.1f   cylinder centre x = %+.4f  y = %+.4f" % (t, cx, cy))
    best = times[int(np.argmax(cys))]
    g, cx, cy = read_time(r, best)
    print("chosen: t = %g (highest cylinder y = %+.4f)" % (best, cy))

    g.point_data["|U|"] = np.linalg.norm(g.point_data["U"], axis=1)
    d = g.compute_derivative(scalars="U", vorticity=True)
    g.point_data["wz"] = d["vorticity"][:, 2]
    wake = g.points[:, 0] > 2.0
    print("wake (x > 2): 99.5 percentile of |wz| = %.2f   |U| max = %.3f   p range = %.3f .. %.3f" % (
        np.percentile(np.abs(g.point_data["wz"][wake]), 99.5),
        g.point_data["|U|"].max(), g.point_data["p"].min(), g.point_data["p"].max()))

    out = os.path.join(out_root, label)
    os.makedirs(out, exist_ok=True)
    for name, f in FIELDS.items():
        p = pv.Plotter(off_screen=True, window_size=SIZE)
        p.set_background("#cfcfcf")
        p.add_mesh(g, scalars=f["key"], cmap=f["cmap"], clim=f["clim"], show_edges=False,
                   lighting=False,
                   scalar_bar_args=dict(title=" ", vertical=False, position_x=0.3,
                                        position_y=0.04, width=0.4, height=0.06, color="black"))
        disc = pv.Circle(radius=0.5, resolution=120)
        disc.translate((cx, cy, 0.2), inplace=True)
        p.add_mesh(disc, color="#303030", lighting=False)
        p.camera.parallel_projection = True
        p.camera.focal_point = (XC, YC, 0.05)
        p.camera.position = (XC, YC, 50.0)
        p.camera.up = (0, 1, 0)
        p.camera.parallel_scale = HALF_HEIGHT
        p.add_text("%s   %s   t = %g   cylinder y = %+.3f D" % (label, f["caption"], best, cy),
                   position="upper_left", font_size=12, color="black")
        path = os.path.join(out, name + ".png")
        p.screenshot(path)
        p.close()
        print("saved", path)


if __name__ == "__main__":
    main()
