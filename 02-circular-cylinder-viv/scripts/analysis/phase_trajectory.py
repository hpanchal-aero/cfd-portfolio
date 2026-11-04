#!/usr/bin/env python3
"""phase_trajectory.py -- phase lift/displacement, in-line amplitude and x-y trajectory content
of the settled (and modulated) cases of the U_r sweep. Post-processing only, no new run.

Usage:  phase_trajectory.py            all rows of results/sweep/sweep_summary.csv (writes results/sweep/phase_trajectory.csv)
        phase_trajectory.py Ur6 Ur8    only the named labels (prints, writes nothing)
Run from the project directory (02-circular-cylinder-viv).

Data:   body position (x, y) from the run logs and Cl from forceCoeffs.dat, via the readers of body_motion.py;
        window of each case = column "window" of the sweep CSV; whole periods = first to last upward crossing
        of y - mean(y) inside the window (same rule as body_motion.py).
Method: least-squares sinusoid fit over the whole periods, with the body frequency f = n_periods/(last-first crossing):
          y  = c + Ay cos(wt - py),   Cl = c + Ac cos(wt - pc),   x = c + Ax1 cos(wt - ..) + Ax2 cos(2wt - ..)
        phase (literature convention) = py - pc, wrapped to [-180, 180) deg;  positive = lift leads displacement.
        The Cl of forceCoeffs.dat is the TOTAL fluid force (pressure + viscous), so this is the total-force phase,
        not the vortex-force phase.
        Spread of the phase: the same fit on consecutive blocks of 5 periods (min, max).
        A_x* = (max - min)/2 of x over the whole periods (oscillation amplitude, independent of the origin of X).
Checks: A_y (max-min)/2 and f are compared with the CSV for settled cases (tolerance 0.5 % and 0.2 %).
Read-only apart from the CSV written in the all-rows mode.
"""
import csv
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body_motion as bm  # noqa: E402

CSV_IN = "results/sweep/sweep_summary.csv"
CSV_OUT = "results/sweep/phase_trajectory.csv"
BASE = "moving_Re150_%s_dom-big_medium_dt0.0025_pre"
DIRS = {
    "Ur3": BASE % "Ur3", "Ur3.5": BASE % "Ur3.5", "Ur4": BASE % "Ur4", "Ur4.5": BASE % "Ur4.5",
    "Ur5": "moving_Re150_Ur5_dom-big_medium_dt0.0025",  # anchor at the start position (no _pre), mean_x 0.32 in the CSV
    "Ur6": BASE % "Ur6", "Ur6_fine": "moving_Re150_Ur6_dom-big_fine_dt0.0025_pre",
    "Ur6_ms2": BASE % "Ur6" + "_ms2",
    "Ur7": BASE % "Ur7", "Ur7.5": BASE % "Ur7.5", "Ur7.75": BASE % "Ur7.75", "Ur8": BASE % "Ur8",
    "Ur11": BASE % "Ur11", "Ur17": BASE % "Ur17",
}
TOL_A, TOL_F = 0.5, 0.2  # percent


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def harm(s, sig, freqs):
    cols = [np.ones_like(s)]
    for fr in freqs:
        cols += [np.cos(2 * np.pi * fr * s), np.sin(2 * np.pi * fr * s)]
    M = np.column_stack(cols)
    coef = np.linalg.lstsq(M, sig, rcond=None)[0]
    res = sig - M @ coef
    return coef, res


def ap(a, b):
    return np.hypot(a, b), np.degrees(np.arctan2(b, a))


def fit_block(tt, xx, yy, cc, f):
    s = tt - tt[0]
    cy, ry = harm(s, yy, [f])
    cl, rc = harm(s, cc, [f])
    cx, _ = harm(s, xx, [f, 2 * f])
    Ay, py = ap(cy[1], cy[2])
    Ac, pc = ap(cl[1], cl[2])
    Ax1, _ = ap(cx[1], cx[2])
    Ax2, _ = ap(cx[3], cx[4])
    return dict(Ay=Ay, Ac=Ac, Ax1=Ax1, Ax2=Ax2, phase=wrap(py - pc),
                res_y=100 * np.std(ry) / Ay, res_cl=100 * np.std(rc) / Ac)


def analyse(label, row, t, x, y, ft, cl):
    t0, t1 = [float(v) for v in row["window"].split("-")]
    m = (t >= t0) & (t <= t1)
    zc = bm.upward_crossings(t[m], y[m] - np.mean(y[m]))
    if len(zc) < 2:
        sys.exit("%s: fewer than two crossings in the window" % label)
    a, b = zc[0], zc[-1]
    n = len(zc) - 1
    f = n / (b - a)
    mw = (t >= a) & (t <= b)
    tt, xx, yy = t[mw], x[mw], y[mw]
    if tt[0] < ft[0] or tt[-1] > ft[-1]:
        sys.exit("%s: force record does not cover the window" % label)
    cc = np.interp(tt, ft, cl)
    whole = fit_block(tt, xx, yy, cc, f)
    blocks = []
    starts = list(range(0, n - 4, 5)) if n >= 5 else []
    for i in starts:
        mb = (t >= zc[i]) & (t <= zc[i + 5])
        tb = t[mb]
        blocks.append(fit_block(tb, x[mb], y[mb], np.interp(tb, ft, cl), 5.0 / (zc[i + 5] - zc[i]))["phase"])
    if not blocks:
        blocks = [whole["phase"]]
    out = dict(label=label, U_r=row["U_r"], kind=row["kind"], window=row["window"], n_periods=n, f=f,
               A_y=(yy.max() - yy.min()) / 2.0, A_x_pp2=(xx.max() - xx.min()) / 2.0,
               A_x_f=whole["Ax1"], A_x_2f=whole["Ax2"], A_cl_fit=whole["Ac"],
               phase_deg=whole["phase"], phase_blk_min=min(blocks), phase_blk_max=max(blocks), n_blocks=len(blocks),
               res_y_pct=whole["res_y"], res_cl_pct=whole["res_cl"])
    flags = []
    if row["kind"] != "modulated":
        dA = 100 * (out["A_y"] - float(row["A_high"])) / float(row["A_high"])
        dF = 100 * (f - float(row["f"])) / float(row["f"])
        out["dA_csv_pct"], out["df_csv_pct"] = dA, dF
        if abs(dA) > TOL_A:
            flags.append("A_y differs from CSV by %+.2f %%" % dA)
        if abs(dF) > TOL_F:
            flags.append("f differs from CSV by %+.2f %%" % dF)
    else:
        out["dA_csv_pct"], out["df_csv_pct"] = "", ""
    out["flags"] = "; ".join(flags)
    return out


def main():
    rows = list(csv.DictReader(open(CSV_IN)))
    want = sys.argv[1:]
    sel = [r for r in rows if (not want or r["label"] in want)]
    if not sel:
        sys.exit("no matching label")
    results = []
    for r in sel:
        lab = r["label"]
        if lab not in DIRS:
            sys.exit("no case directory for " + lab)
        case = "cases/" + DIRS[lab]
        t, x, y = bm.read_state(bm.chunk_logs(case))
        fc, _ = bm.read_forces(case)
        ft, idx = np.unique(fc[:, 0], return_index=True)
        o = analyse(lab, r, t, x, y, ft, fc[idx, 3])
        results.append(o)
        print("%-9s %-10s win %-8s %2d periods  f %.5f  A_y %.4f  A_x* %.4f (fit f %.4f, 2f %.4f)  |Cl| fit %.4f"
              % (lab, o["kind"], o["window"], o["n_periods"], o["f"], o["A_y"], o["A_x_pp2"], o["A_x_f"], o["A_x_2f"], o["A_cl_fit"]))
        print("          phase (lift leads +) %+8.3f deg, 5-period blocks %+8.3f .. %+8.3f (%d blocks); fit residual y %.2f %%, Cl %.2f %%; vs CSV: dA %s, df %s  %s"
              % (o["phase_deg"], o["phase_blk_min"], o["phase_blk_max"], o["n_blocks"], o["res_y_pct"], o["res_cl_pct"],
                 ("%+.2f %%" % o["dA_csv_pct"]) if o["dA_csv_pct"] != "" else "n/a",
                 ("%+.2f %%" % o["df_csv_pct"]) if o["df_csv_pct"] != "" else "n/a",
                 ("FLAG: " + o["flags"]) if o["flags"] else "OK"))
    if not want:
        keys = list(results[0].keys())
        with open(CSV_OUT, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for o in results:
                w.writerow({k: (("%.6g" % v) if isinstance(v, float) else v) for k, v in o.items()})
        print("wrote " + CSV_OUT)


if __name__ == "__main__":
    main()
