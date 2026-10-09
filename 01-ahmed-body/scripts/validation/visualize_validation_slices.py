#!/usr/bin/python3
"""y ~ 0 symmetry-plane slices of iteration-averaged U_x/U_inf and Cp for one case.
Identical camera and colour limits for every case (so cases are comparable).
Cp = 2*pMean/U_inf^2 (p is kinematic, rho = 1 convention in these cases).
Cp colour map: diverging (coolwarm), neutral colour placed at Cp = 0 on the fixed
asymmetric limits, so the undisturbed free stream renders neutral, blue = suction,
red = overpressure. The fields are cell-centred and interpolated to points for
the slice, so the coarse far-field mesh appears blocky.
Usage: visualize_validation_slices.py --vtk F --patch P --U 40 --label val25_40ms --out-dir D"""
import argparse, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyvista as pv

UX_LIM = (-0.4, 1.6)     # U_x / U_inf
CP_LIM = (-2.5, 1.0)     # Cp
Y0 = 5.0e-4              # slice just off the symmetry plane [m]
XC, ZC, HALF_H = 1.0, 0.36, 0.40   # view centre x, z and half-height [m]


def centred_coolwarm(lim):
    """coolwarm with its neutral midpoint moved to the value 0 inside lim = (lo, hi)."""
    assert lim[0] < 0.0 < lim[1]
    f0 = -lim[0] / (lim[1] - lim[0])           # fraction of the range at value 0
    t = np.linspace(0.0, 1.0, 256)
    src = np.where(t < f0, 0.5 * t / f0, 0.5 + 0.5 * (t - f0) / (1.0 - f0))
    return matplotlib.colors.ListedColormap(plt.get_cmap("coolwarm")(src), name="coolwarm_centred")


ap = argparse.ArgumentParser()
ap.add_argument("--vtk", required=True)
ap.add_argument("--patch", required=True)
ap.add_argument("--U", type=float, required=True)
ap.add_argument("--label", required=True)
ap.add_argument("--out-dir", required=True)
a = ap.parse_args()
os.makedirs(a.out_dir, exist_ok=True)

m = pv.read(a.vtk)
sl = m.slice(normal=(0, 1, 0), origin=(0, Y0, 0))
sl = sl.cell_data_to_point_data()
U = np.asarray(sl["UMean"])
sl["Ux_over_Uinf"] = U[:, 0] / a.U
sl["Cp"] = 2.0 * np.asarray(sl["pMean"]) / a.U ** 2
print("%s: slice points %d  Ux/U range %.3f..%.3f  Cp range %.3f..%.3f" %
      (a.label, sl.n_points, sl["Ux_over_Uinf"].min(), sl["Ux_over_Uinf"].max(), sl["Cp"].min(), sl["Cp"].max()))
body = pv.read(a.patch).slice(normal=(0, 1, 0), origin=(0, 0.02, 0))

FIELDS = (
    ("Ux_over_Uinf", UX_LIM, "RdYlBu_r", "U_x / U_inf (mean)", {}),
    ("Cp", CP_LIM, centred_coolwarm(CP_LIM), "Cp (mean)", dict(n_labels=8, fmt="%.1f")),
)

for name, lim, cmap, title, bar_extra in FIELDS:
    pl = pv.Plotter(off_screen=True, window_size=(2400, 700))
    bar = dict(title=" ", vertical=False, width=0.3, position_x=0.35, position_y=0.04)
    bar.update(bar_extra)
    pl.add_mesh(sl, scalars=name, cmap=cmap, clim=lim, show_scalar_bar=True, scalar_bar_args=bar)
    pl.add_mesh(body, color="black", line_width=2)
    pl.add_text("%s   y = %.1f mm   %s" % (a.label, 1000 * Y0, title), position="upper_left", font_size=11)
    pl.camera_position = [(XC, -5.0, ZC), (XC, 0.0, ZC), (0, 0, 1)]
    pl.camera.parallel_projection = True
    pl.camera.parallel_scale = HALF_H
    out = os.path.join(a.out_dir, "slice_%s_%s.png" % (a.label, name))
    pl.screenshot(out)
    pl.close()
    print("wrote", out)
