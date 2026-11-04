#!/usr/bin/env python3
"""make_grid.py -- one comparison figure of a field for all 13 cases, read from results/figures/<label>/<field>.png.

Usage (user packages are needed, so no -I):
    /usr/bin/python3 -E -P scripts/viz/make_grid.py [vorticity|pressure|velocity] [<figures_root>] [<out_dir>]

Writes <out_dir>/<field>_grid.png (default results/comparisons). No new simulation or rendering: the tiles are the
stills made by flow_snapshots.py (same view and colour limits in every tile, each at the highest cylinder y of the last
20 time units of its case).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

ORDER = [("Ur3", "U_r = 3"), ("Ur3.5", "U_r = 3.5 (modulated)"), ("Ur4", "U_r = 4 (modulated)"),
         ("Ur4.5", "U_r = 4.5"), ("Ur5", "U_r = 5"), ("Ur6", "U_r = 6"), ("Ur6_ms2", "U_r = 6, m* = 2"),
         ("Ur7", "U_r = 7"), ("Ur7.5", "U_r = 7.5"), ("Ur7.75", "U_r = 7.75"), ("Ur8", "U_r = 8"),
         ("Ur11", "U_r = 11"), ("Ur17", "U_r = 17")]
SCALE = {"vorticity": "spanwise vorticity w_z D/U, colour scale -3.5 .. +3.5",
         "pressure": "pressure p/(rho U^2), colour scale -1.3 .. +1.3",
         "velocity": "speed |U|/U, colour scale 0 .. 1.7"}

field = sys.argv[1] if len(sys.argv) > 1 else "vorticity"
root = sys.argv[2] if len(sys.argv) > 2 else "results/figures"
out = sys.argv[3] if len(sys.argv) > 3 else "results/comparisons"
if field not in SCALE:
    sys.exit("field must be one of %s" % list(SCALE))
os.makedirs(out, exist_ok=True)

fig, axs = plt.subplots(4, 4, figsize=(20, 11.4), facecolor="black")
for ax in axs.flat:
    ax.axis("off")
for ax, (lab, title) in zip(axs.flat, ORDER):
    ax.imshow(mpimg.imread(os.path.join(root, lab, field + ".png")))
    ax.set_title(title, color="white", fontsize=13)
note = axs.flat[len(ORDER)]
note.text(0.02, 0.5, "Re 150, 2-DOF, m* = 2.546 (unless marked), zeta = 0\n%s\nsame view and scale in every tile\n"
          "each picture at the highest cylinder y of the\nlast 20 time units of its case\n"
          "modulated cases: one stretch of the cycle" % SCALE[field],
          color="white", ha="left", va="center", fontsize=12, transform=note.transAxes)
fig.subplots_adjust(wspace=0.02, hspace=0.14, left=0.01, right=0.99, top=0.96, bottom=0.01)
path = os.path.join(out, field + "_grid.png")
fig.savefig(path, dpi=100, facecolor="black")
print("saved", path)
