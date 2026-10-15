#!/usr/bin/python3
"""25 deg vs 35 deg: mean Ux/U_inf and Cp on the y ~ 0 symmetry plane, same camera
and colour limits as visualize_validation_slices.py, with the reversed-flow
boundary (Ux = 0) drawn as a black line, plus a table of CFD reversed-flow
extent and area. CFD only: no experimental data is read or drawn.
Cp = 2*pMean/U_inf^2 with p referenced to the outlet value (p = 0), so the
nose stagnation value can differ slightly from the force-based reference.
Usage: compare_slant_wakes.py --vtk25 F --patch25 P --vtk35 F --patch35 P --U 40 --out-dir D"""
import argparse, csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyvista as pv

UX_LIM = (-0.4, 1.6)
CP_LIM = (-2.5, 1.0)
Y0 = 5.0e-4
XC, ZC, HALF_H = 1.0, 0.36, 0.40
X_BASE = 1.044          # rear face of the body [m]
Z_FLOOR = 0.06          # ignore the floor boundary layer when looking for reversed flow
X_SLANT0 = 0.80         # upstream limit used for the slant-region reversed area
Z_SLANT0 = 0.15         # below this the underbody gap, not the slant layer


def centred_coolwarm(lim):
    f0 = -lim[0] / (lim[1] - lim[0])
    t = np.linspace(0.0, 1.0, 256)
    src = np.where(t < f0, 0.5 * t / f0, 0.5 + 0.5 * (t - f0) / (1.0 - f0))
    return matplotlib.colors.ListedColormap(plt.get_cmap("coolwarm")(src), name="coolwarm_centred")


def load_slice(path, U):
    m = pv.read(path)
    sl = m.slice(normal=(0, 1, 0), origin=(0, Y0, 0)).cell_data_to_point_data()
    sl["Ux_over_Uinf"] = np.asarray(sl["UMean"])[:, 0] / U
    sl["Cp"] = 2.0 * np.asarray(sl["pMean"]) / U ** 2
    return sl


def analyse(sl):
    pts = sl.points
    ux = np.asarray(sl["Ux_over_Uinf"])
    w = (ux < 0) & (pts[:, 0] > X_BASE + 1e-3) & (pts[:, 2] > Z_FLOOR)
    wake_end = float(pts[w, 0].max() - X_BASE) if w.any() else float("nan")
    c = sl.point_data_to_cell_data().compute_cell_sizes(length=False, area=True, volume=False)
    ctr = c.cell_centers().points
    rev = np.asarray(c["Ux_over_Uinf"]) < 0
    area = np.asarray(c["Area"])
    a_wake = float(area[rev & (ctr[:, 0] > X_BASE) & (ctr[:, 2] > Z_FLOOR)].sum())
    a_slant = float(area[rev & (ctr[:, 0] > X_SLANT0) & (ctr[:, 0] <= X_BASE) & (ctr[:, 2] > Z_SLANT0)].sum())
    return dict(wake_end_m=wake_end, wake_rev_area_m2=a_wake, slant_rev_area_m2=a_slant, ux_min=float(ux.min()))


ap = argparse.ArgumentParser()
ap.add_argument("--vtk25", required=True)
ap.add_argument("--patch25", required=True)
ap.add_argument("--vtk35", required=True)
ap.add_argument("--patch35", required=True)
ap.add_argument("--U", type=float, required=True)
ap.add_argument("--out-dir", required=True)
a = ap.parse_args()
os.makedirs(a.out_dir, exist_ok=True)

cases = (("25 deg slant", 25, a.vtk25, a.patch25), ("35 deg slant", 35, a.vtk35, a.patch35))
data = []
for label, ang, vtk, patch in cases:
    sl = load_slice(vtk, a.U)
    body = pv.read(patch).slice(normal=(0, 1, 0), origin=(0, 0.02, 0))
    res = analyse(sl)
    res["angle"] = ang
    data.append((label, sl, body, res))
    print("%s: reversed-flow extent behind base %.3f m (%.0f mm), wake reversed area %.4f m^2, slant-region reversed area %.5f m^2, Ux/U min %.3f" %
          (label, res["wake_end_m"], 1000 * res["wake_end_m"], res["wake_rev_area_m2"], res["slant_rev_area_m2"], res["ux_min"]))

with open(os.path.join(a.out_dir, "reversed_flow_25_vs_35.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["angle_deg", "wake_reversed_extent_m", "wake_reversed_area_m2", "slant_region_reversed_area_m2", "Ux_over_Uinf_min"])
    for _, _, _, r in data:
        w.writerow([r["angle"], "%.4f" % r["wake_end_m"], "%.5f" % r["wake_rev_area_m2"], "%.5f" % r["slant_rev_area_m2"], "%.3f" % r["ux_min"]])

FIELDS = (
    ("Ux_over_Uinf", UX_LIM, "RdYlBu_r", "U_x / U_inf (mean); black line: U_x = 0", {}, "ux_25_vs_35.png"),
    ("Cp", CP_LIM, centred_coolwarm(CP_LIM), "Cp (mean)", dict(n_labels=8, fmt="%.1f"), "cp_25_vs_35.png"),
)
for name, lim, cmap, title, bar_extra, fname in FIELDS:
    pl = pv.Plotter(off_screen=True, shape=(2, 1), window_size=(2400, 1400), border=False)
    for row, (label, sl, body, res) in enumerate(data):
        pl.subplot(row, 0)
        bar = dict(title=" ", vertical=False, width=0.3, position_x=0.35, position_y=0.04)
        bar.update(bar_extra)
        pl.add_mesh(sl, scalars=name, cmap=cmap, clim=lim, show_scalar_bar=(row == 1), scalar_bar_args=bar)
        if name == "Ux_over_Uinf":
            line = sl.contour(isosurfaces=[0.0], scalars="Ux_over_Uinf")
            if line.n_points:
                pl.add_mesh(line, color="black", line_width=3)
        pl.add_mesh(body, color="black", line_width=2)
        pl.add_text("%s   y = %.1f mm   %s" % (label, 1000 * Y0, title), position="upper_left", font_size=11)
        pl.camera_position = [(XC, -5.0, ZC), (XC, 0.0, ZC), (0, 0, 1)]
        pl.camera.parallel_projection = True
        pl.camera.parallel_scale = HALF_H
    out = os.path.join(a.out_dir, fname)
    pl.screenshot(out)
    pl.close()
    print("wrote", out)
