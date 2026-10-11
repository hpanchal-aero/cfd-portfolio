#!/usr/bin/env python3
"""
Stationarity and window statistics for a stitched forceCoeffs record
(the CSV written by stitch_force_segments.py).

For each window start s (window = [s, END], both ends inclusive):
    n, mean and std of Cd and Cl, and
    drift/std = (least-squares slope of the signal vs t) * (t_last - t_first)
                / sample std (ddof=1)
For each explicit window "a:b":
    n, mean/std of Cd and Cl, and the sub-window spread
    (max - min of sub-window means) / overall mean * 100 for
    --nsub equal-count sub-windows and --nsub-time equal-time sub-windows.
The spreads are variability of the mean between chunks of the record. They are
NOT confidence intervals (samples are autocorrelated).

Usage:
    stationarity_report.py --csv stitched.csv --end 0.30
        --starts 0.06 0.10 0.14 0.18 0.20 0.22
        --windows 0.14:0.30 0.18:0.30 [--signal Cd] [--nsub 5] [--nsub-time 4]
"""
import argparse
import sys

import numpy as np

EPS = 1e-12


def load(path):
    with open(path, encoding="utf-8") as fh:
        names = fh.readline().strip().split(",")
    return names, np.loadtxt(path, delimiter=",", skiprows=1)


def window(arr, t0, t1):
    m = (arr[:, 0] >= t0 - EPS) & (arr[:, 0] <= t1 + EPS)
    return arr[m]


def drift_over_std(t, y):
    slope = np.polyfit(t, y, 1)[0]
    return slope * (t[-1] - t[0]) / y.std(ddof=1)


def spread_equal_count(y, k):
    means = [p.mean() for p in np.array_split(y, k)]
    return (max(means) - min(means)) / y.mean() * 100.0, means


def spread_equal_time(t, y, k):
    edges = np.linspace(t[0], t[-1], k + 1)
    idx = np.digitize(t, edges[1:-1])
    means = [y[idx == i].mean() for i in range(k)]
    return (max(means) - min(means)) / y.mean() * 100.0, means


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--end", type=float, help="end of record/window (default: last time)")
    ap.add_argument("--starts", type=float, nargs="*", default=[])
    ap.add_argument("--windows", nargs="*", default=[], help="a:b pairs")
    ap.add_argument("--signal", default="Cd", help="column used for drift/std")
    ap.add_argument("--nsub", type=int, default=5)
    ap.add_argument("--nsub-time", type=int, default=4)
    a = ap.parse_args()

    names, arr = load(a.csv)
    for need in (a.signal, "Cd", "Cl"):
        if need not in names:
            sys.exit(f"column {need} not in {names}")
    ci = {n: i for i, n in enumerate(names)}
    end = a.end if a.end is not None else arr[-1, 0]
    rec = arr[arr[:, 0] <= end + EPS]
    print(f"record: {len(rec)} rows, t {rec[0,0]:.6g} .. {rec[-1,0]:.6g}  (END = {end:g})")

    if a.starts:
        print(f"\ndrift/std of {a.signal} by window start (window = [start, {end:g}])")
        print(f"{'start':>7} {'n':>7} {'Cd mean':>10} {'Cd std':>9} {'Cl mean':>10} {'drift/std':>10}")
        means = []
        for s in a.starts:
            w = window(rec, s, end)
            if len(w) < 3:
                print(f"{s:7g}  too few rows")
                continue
            t, y = w[:, 0], w[:, ci[a.signal]]
            means.append((w[:, ci["Cd"]].mean(), w[:, ci["Cl"]].mean()))
            print(f"{s:7g} {len(w):7d} {w[:,ci['Cd']].mean():10.5f} {w[:,ci['Cd']].std(ddof=1):9.5f} "
                  f"{w[:,ci['Cl']].mean():10.5f} {drift_over_std(t, y):+10.3f}")
        if len(means) > 1:
            m = np.array(means)
            print(f"variation of the mean across these starts: "
                  f"Cd {np.ptp(m[:,0]):.5f} ({np.ptp(m[:,0])/m[:,0].mean()*100:.2f} %), "
                  f"Cl {np.ptp(m[:,1]):.5f}")

    for spec in a.windows:
        t0, t1 = (float(x) for x in spec.split(":"))
        w = window(rec, t0, t1)
        t = w[:, 0]
        cd, cl = w[:, ci["Cd"]], w[:, ci["Cl"]]
        print(f"\nwindow {spec}: n = {len(w)}")
        print(f"  Cd mean {cd.mean():.5f} std {cd.std(ddof=1):.5f}   "
              f"Cl mean {cl.mean():.5f} std {cl.std(ddof=1):.5f}")
        sp, mm = spread_equal_count(cd, a.nsub)
        print(f"  Cd spread, {a.nsub} equal-count sub-windows: {sp:.2f} %  means " +
              ", ".join(f"{x:.5f}" for x in mm))
        sp, mm = spread_equal_time(t, cd, a.nsub_time)
        print(f"  Cd spread, {a.nsub_time} equal-time sub-windows:  {sp:.2f} %  means " +
              ", ".join(f"{x:.5f}" for x in mm))
        sp, _ = spread_equal_count(cd, a.nsub_time)
        print(f"  Cd spread, {a.nsub_time} equal-count sub-windows: {sp:.2f} %")
        sp, _ = spread_equal_time(t, cd, a.nsub)
        print(f"  Cd spread, {a.nsub} equal-time sub-windows:  {sp:.2f} %")


if __name__ == "__main__":
    main()
