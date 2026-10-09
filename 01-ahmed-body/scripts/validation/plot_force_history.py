#!/usr/bin/python3
"""Cd and Cl history of steady (SIMPLEC) validation cases, with the averaging window shaded.
Restart segments are stitched from postProcessing/forces/<start>/forceCoeffs.dat in
numeric order of the start directory; for an iteration written by several segments
the row from the LATER segment is used. Iterations before --start are not plotted
(start-up transient). Window statistics use iterations --win0 .. --win1 inclusive.
Coefficients are half-body values normalised with Aref = 0.056016 (= full frontal
area / 2, half-domain), so they equal full-body coefficients.
Usage: plot_force_history.py --case label,case_dir [--case ...] --out F.png
       [--start 50] [--win0 1000] [--win1 2000]"""
import argparse, glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(case_dir):
    pat = os.path.join(case_dir, "postProcessing", "forces", "*", "forceCoeffs.dat")
    files = sorted(glob.glob(pat), key=lambda p: float(p.split(os.sep)[-2]))
    if not files:
        raise SystemExit("no forceCoeffs.dat found under " + case_dir)
    rows = {}
    for f in files:
        for ln in open(f):
            if ln.startswith("#") or not ln.strip():
                continue
            c = ln.split()
            rows[int(float(c[0]))] = (float(c[2]), float(c[3]))   # Cd, Cl
    t = np.array(sorted(rows))
    cd = np.array([rows[k][0] for k in t])
    cl = np.array([rows[k][1] for k in t])
    return t, cd, cl, len(files), int(np.count_nonzero(np.diff(t) != 1))


ap = argparse.ArgumentParser()
ap.add_argument("--case", action="append", required=True, help="label,case_dir (repeatable)")
ap.add_argument("--out", required=True)
ap.add_argument("--start", type=int, default=50)
ap.add_argument("--win0", type=int, default=1000)
ap.add_argument("--win1", type=int, default=2000)
a = ap.parse_args()

colors = ["tab:blue", "tab:red", "tab:green", "tab:purple", "tab:orange"]
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
print("%-22s %6s %5s %6s %10s %10s %10s %10s" %
      ("case", "files", "gaps", "N_win", "mean Cd", "std Cd", "mean Cl", "std Cl"))
for i, spec in enumerate(a.case):
    label, cdir = spec.split(",", 1)
    t, cd, cl, nfiles, ngaps = load(os.path.expanduser(cdir))
    w = (t >= a.win0) & (t <= a.win1)
    print("%-22s %6d %5d %6d %10.5f %10.5f %10.5f %10.5f" %
          (label, nfiles, ngaps, w.sum(), cd[w].mean(), cd[w].std(), cl[w].mean(), cl[w].std()))
    m = t >= a.start
    axes[0].plot(t[m], cd[m], lw=0.8, color=colors[i % len(colors)],
                 label="%s   mean %.5f  std %.5f" % (label, cd[w].mean(), cd[w].std()))
    axes[1].plot(t[m], cl[m], lw=0.8, color=colors[i % len(colors)],
                 label="%s   mean %.4f  std %.4f" % (label, cl[w].mean(), cl[w].std()))

for ax, name in zip(axes, ("Cd", "Cl")):
    ax.axvspan(a.win0, a.win1, color="0.5", alpha=0.10, lw=0)
    ax.set_ylabel(name)
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
axes[0].set_title("Force history (half-domain, Aref = 0.056016); shaded = averaging window %d-%d" %
                  (a.win0, a.win1))
axes[1].set_xlabel("iteration")
fig.tight_layout()
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
fig.savefig(a.out, dpi=150)
print("wrote", a.out)
