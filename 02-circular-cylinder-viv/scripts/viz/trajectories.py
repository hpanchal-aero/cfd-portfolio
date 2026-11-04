#!/usr/bin/env python3
"""trajectories.py -- path of the cylinder centre (x - mean(x) against y) for the cases of the U_r sweep.

Run from the project directory:  /usr/bin/python3 -E -P scripts/viz/trajectories.py
Reads    results/sweep/phase_trajectory.csv (windows, A_y, A_x*), the run logs through body_motion.py.
Writes   results/comparisons/trajectories.png
Shows    the last NPER body periods inside the window of each case (whole periods between upward crossings
         of y - mean(y)). Same limits in every panel: y in +-0.7 D, x - mean(x) in +-0.04 D. The x axis is
         stretched about 17 times relative to y (x span 0.08 D, y span 1.4 D), so the panels are NOT to scale.
         A warning is printed if a path leaves the x limits (it would be clipped).
"""
import csv
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "analysis"))
import body_motion as bm  # noqa: E402
import phase_trajectory as pt  # noqa: E402

CSV = "results/sweep/phase_trajectory.csv"
OUT = "results/comparisons/trajectories.png"
LABELS = ["Ur3", "Ur3.5", "Ur4", "Ur4.5", "Ur5", "Ur6", "Ur6_ms2", "Ur7", "Ur7.5", "Ur7.75", "Ur8", "Ur11", "Ur17"]
NPER = 4
XHALF = 0.04
YHALF = 0.7


def title(r, lab):
    s = "U_r %s" % r["U_r"]
    if lab == "Ur6_ms2":
        s += ", m* = 2"
    if r["kind"] == "modulated":
        s += " (modulated)"
    if r["kind"] == "modulated":
        return "%s\nA_y* max %.3f, x half-range %.4f" % (s, float(r["A_y"]), float(r["A_x_pp2"]))
    return "%s\nA_y* %.3f, A_x* %.4f" % (s, float(r["A_y"]), float(r["A_x_pp2"]))


def main():
    rows = {r["label"]: r for r in csv.DictReader(open(CSV))}
    fig, axs = plt.subplots(4, 4, figsize=(13, 13))
    axs = axs.ravel()
    for i, (ax, lab) in enumerate(zip(axs, LABELS)):
        r = rows[lab]
        t, x, y = bm.read_state(bm.chunk_logs("cases/" + pt.DIRS[lab]))
        t0, t1 = [float(v) for v in r["window"].split("-")]
        m = (t >= t0) & (t <= t1)
        zc = bm.upward_crossings(t[m], y[m] - np.mean(y[m]))
        if len(zc) < NPER + 1:
            sys.exit("%s: not enough crossings" % lab)
        mm = (t >= zc[-NPER - 1]) & (t <= zc[-1])
        xs, ys = x[mm], y[mm]
        xm = np.mean(xs)
        dev = np.max(np.abs(xs - xm))
        print("%-8s last %d periods t = %.2f .. %.2f, max |x - mean| = %.4f%s"
              % (lab, NPER, zc[-NPER - 1], zc[-1], dev, "   WARNING: outside x limit" if dev > XHALF else ""))
        ax.axhline(0, color="0.85", lw=0.6)
        ax.axvline(0, color="0.85", lw=0.6)
        ax.plot(xs - xm, ys, lw=0.9, color="C0")
        ax.set_xlim(-XHALF, XHALF)
        ax.set_ylim(-YHALF, YHALF)
        ax.set_title(title(r, lab), fontsize=9)
        if i % 4 == 0:
            ax.set_ylabel("y / D")
        if i >= 9:
            ax.set_xlabel("x - mean(x) [D], axis stretched")
    for ax in axs[len(LABELS):]:
        ax.axis("off")
    fig.suptitle("Path of the cylinder centre, last %d body periods of each window (Re 150, m* 2.546 unless stated)\n"
                 "same limits in all panels; x axis stretched about 17x relative to y, not to scale" % NPER, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=150)
    print("wrote " + OUT)


if __name__ == "__main__":
    main()
