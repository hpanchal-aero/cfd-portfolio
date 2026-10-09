#!/usr/bin/python3
"""Profile plots from comparison_points.csv written by sample_ercoftac_y0.py.
Columns: set(0=global,1=focus), x_mm, z_mm, valid, U_exp, U_cfd, W_exp, W_cfd, k_exp, k_cfd
Each station is drawn as U(z) shifted by x (profile scale = SCALE mm per m/s)."""
import argparse, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCALE = 3.0  # mm of x-offset per m/s


def panel(ax, d, xs, title, ucol_e, ucol_c):
    for x in xs:
        s = d[d[:, 1] == x]
        s = s[np.argsort(s[:, 2])]
        ax.plot(x + SCALE * s[:, ucol_e], s[:, 2], "ko", ms=3, label="ERCOFTAC Exp2" if x == xs[0] else None)
        ax.plot(x + SCALE * s[:, ucol_c], s[:, 2], "-", color="tab:red", lw=1.2, label="CFD (UMean)" if x == xs[0] else None)
        ax.axvline(x, color="0.8", lw=0.6)
    ax.set_xlabel("x_data [mm] (profile = x + %.0f mm per m/s)" % SCALE)
    ax.set_ylabel("z [mm]")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    d = np.loadtxt(a.csv, delimiter=",")
    d = d[d[:, 3] == 1]
    slant = d[(d[:, 0] == 1) & (d[:, 1] >= -201.2) & (d[:, 1] <= 0)]
    wake = d[(d[:, 0] == 0) & (d[:, 1] > 0) & (d[:, 1] <= 338)]
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
    panel(ax[0], slant, sorted(set(slant[:, 1])), "Slant stations: U(z), %s" % a.label, 4, 5)
    panel(ax[1], wake, sorted(set(wake[:, 1])), "Wake stations: U(z), %s" % a.label, 4, 5)
    fig.tight_layout()
    out = os.path.join(a.out_dir, "U_profiles_%s.png" % a.label)
    fig.savefig(out, dpi=150)
    print("wrote", out)
    # per-station U difference at the lowest-z valid points of the slant (diagnostic)
    print("\nslant: z of the 3 lowest points, U_exp vs U_cfd (m/s)")
    for x in sorted(set(slant[:, 1])):
        s = slant[slant[:, 1] == x]
        s = s[np.argsort(s[:, 2])][:3]
        print("x %7.1f  " % x + "  ".join("z %5.0f: %5.1f vs %5.1f" % (r[2], r[4], r[5]) for r in s))


if __name__ == "__main__":
    main()
