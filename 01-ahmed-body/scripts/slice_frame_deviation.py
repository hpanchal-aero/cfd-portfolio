#!/usr/bin/env python3
"""
Frame-to-frame deviation of a saved cutPlaneSurface slice (point data p and U).

For each named frame set (--set LABEL:t1,t2,...) and a rectangular "wake" mask
(x in [xmin, xmax], z in [zmin, zmax], points of the slice, unweighted):
    - mean field over the frames of the set;
    - per frame: RMS deviation of p and Ux from that mean over the mask points,
      wake-mean and wake-std of Ux, the minimum Ux on the near-ground row
      (points with |z - zrow| <= ztol inside the mask) and its x, and the
      whole-slice minimum pressure;
    - max/min ratio of the RMS deviations over the set.
All frames must share the same point set (checked).

Defaults (x 1.044-6.264, z 0-0.8, near-ground row z = 0.01044) are an INFERRED
wake region: the README does not define it. Checked against the 35 deg values
published in the README: near-ground minima and whole-slice pressure minima are
reproduced exactly; p and Ux RMS deviations to within about 3 %; wake-mean Ux
is about 0.05 m/s below the published values. The wall row (z = 0, 330 points
at x >= 1.044) must stay in the mask: excluding it moves the wake mean/std
far from the published values.

The README does not define the wake region, so --scan ranks candidate masks by
how well the wake-mean and wake-std of Ux over the frames of --scan-set match
published ranges (--target-mean, --target-std). The RMS-deviation values must
then be checked against numbers that were NOT used in that fit.

Usage:
    slice_frame_deviation.py --case CASE_DIR --set first8:0.091,0.102,...
        --set stationary:0.204,0.215,... --scan --scan-set stationary
        --target-mean 55.72 55.81 --target-std 12.21 12.35
    slice_frame_deviation.py --case CASE_DIR --set ... --xmin 1.044 --xmax 6.264 --zmax 2.088
"""
import argparse
import itertools
import os
import sys

import numpy as np
import pyvista as pv


def load_frame(case, t):
    path = os.path.join(case, "postProcessing", "cutPlaneSurface", f"{t:g}", "cutPlane.vtk")
    if not os.path.isfile(path):
        sys.exit(f"missing slice file: {path}")
    m = pv.read(path)
    return (np.asarray(m.points), np.asarray(m.point_data["p"]),
            np.asarray(m.point_data["U"])[:, 0])


def load_set(case, spec):
    label, times = spec.split(":")
    ts = [float(x) for x in times.split(",")]
    pts0, ps, us = None, [], []
    for t in ts:
        pts, p, ux = load_frame(case, t)
        if pts0 is None:
            pts0 = pts
        elif pts.shape != pts0.shape or not np.allclose(pts, pts0, atol=1e-9):
            sys.exit(f"frame t={t:g}: point set differs from the first frame")
        ps.append(p)
        us.append(ux)
    return label, ts, pts0, np.array(ps), np.array(us)


def mask_of(pts, xmin, xmax, zmin, zmax):
    return ((pts[:, 0] >= xmin) & (pts[:, 0] <= xmax) &
            (pts[:, 2] >= zmin) & (pts[:, 2] <= zmax))


def wake_stats(UX, mask):
    v = UX[:, mask]
    return v.mean(axis=1), v.std(axis=1, ddof=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True)
    ap.add_argument("--set", action="append", required=True, dest="sets")
    ap.add_argument("--xmin", type=float, default=1.044)
    ap.add_argument("--xmax", type=float, default=6.264)
    ap.add_argument("--zmin", type=float, default=0.0)
    ap.add_argument("--zmax", type=float, default=0.8)
    ap.add_argument("--zrow", type=float, default=0.01044)
    ap.add_argument("--ztol", type=float, default=1e-4)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--scan-set")
    ap.add_argument("--target-mean", type=float, nargs=2)
    ap.add_argument("--target-std", type=float, nargs=2)
    ap.add_argument("--scan-xmin", type=float, nargs="+", default=[1.044, 1.05, 1.1, 1.15, 1.2])
    ap.add_argument("--scan-xmax", type=float, nargs="+", default=[2.0, 2.5, 3.0, 4.0, 5.0, 6.264])
    ap.add_argument("--scan-zmax", type=float, nargs="+", default=[0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.088])
    a = ap.parse_args()

    data = [load_set(a.case, s) for s in a.sets]

    if a.scan:
        if not (a.scan_set and a.target_mean and a.target_std):
            sys.exit("--scan needs --scan-set, --target-mean and --target-std")
        label, ts, pts, P, UX = next(d for d in data if d[0] == a.scan_set)
        res = []
        for xmin, xmax, zmax in itertools.product(a.scan_xmin, a.scan_xmax, a.scan_zmax):
            m = mask_of(pts, xmin, xmax, a.zmin, zmax)
            if m.sum() < 100:
                continue
            wm, ws = wake_stats(UX, m)
            err = (abs(wm.min() - a.target_mean[0]) + abs(wm.max() - a.target_mean[1]) +
                   abs(ws.min() - a.target_std[0]) + abs(ws.max() - a.target_std[1]))
            res.append((err, xmin, xmax, zmax, int(m.sum()), wm.min(), wm.max(), ws.min(), ws.max()))
        res.sort()
        print(f"scan of {len(res)} masks on set '{label}'; target mean {a.target_mean}, std {a.target_std}")
        print(f"{'err':>7} {'xmin':>6} {'xmax':>6} {'zmax':>6} {'n':>6}  mean range        std range")
        for r in res[:10]:
            print(f"{r[0]:7.3f} {r[1]:6.3f} {r[2]:6.3f} {r[3]:6.3f} {r[4]:6d}  "
                  f"{r[5]:.2f}-{r[6]:.2f}   {r[7]:.2f}-{r[8]:.2f}")
        return

    for label, ts, pts, P, UX in data:
        m = mask_of(pts, a.xmin, a.xmax, a.zmin, a.zmax)
        print(f"\n=== set '{label}': {len(ts)} frames, wake mask x[{a.xmin:g},{a.xmax:g}] "
              f"z[{a.zmin:g},{a.zmax:g}] -> {int(m.sum())} of {len(pts)} points")
        mp, mu = P[:, m].mean(axis=0), UX[:, m].mean(axis=0)
        rms_p = np.sqrt(((P[:, m] - mp) ** 2).mean(axis=1))
        rms_u = np.sqrt(((UX[:, m] - mu) ** 2).mean(axis=1))
        wm, ws = wake_stats(UX, m)
        ng = m & (np.abs(pts[:, 2] - a.zrow) <= a.ztol)
        print(f"{'t':>7} {'rmsDev p':>9} {'rmsDev Ux':>10} {'wake Ux':>8} {'wake std':>9} "
              f"{'min Ux':>8} {'at x':>7} {'p min':>9}")
        for k, t in enumerate(ts):
            if ng.any():
                j = np.argmin(UX[k, ng])
                mn, mx = UX[k, ng][j], pts[ng, 0][j]
            else:
                mn, mx = float("nan"), float("nan")
            print(f"{t:7g} {rms_p[k]:9.2f} {rms_u[k]:10.3f} {wm[k]:8.2f} {ws[k]:9.2f} "
                  f"{mn:8.2f} {mx:7.3f} {P[k].min():9.1f}")
        if len(ts) > 1:
            print(f"max/min ratio of RMS deviation: p {rms_p.max()/rms_p.min():.2f}, "
                  f"Ux {rms_u.max()/rms_u.min():.2f}")


if __name__ == "__main__":
    main()
