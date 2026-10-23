#!/usr/bin/env python3
"""compare_histories.py -- point-by-point comparison of two forceCoeffs.dat histories.

Usage:  compare_histories.py <ref.dat> <test.dat> <t0> <t1> [dt]

Joins the two files on time (integer multiples of dt, default 0.0025), keeps t0 <= t <= t1 and prints
  1. sample counts and the Cl rms of the reference in the window (scale for the differences),
  2. Cd, Cl of both runs and their differences once per time unit,
  3. rms differences in three segments: [t0, t0+2], [t0+2, t0+10], [t0+10, t1],
  4. times of the upward zero crossings of Cl in both runs and their differences.
Columns of forceCoeffs.dat: Time Cm Cd Cl Cl(f) Cl(r).  Read-only; writes nothing.
"""
import sys
import numpy as np


def load(path):
    rows = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        rows.append([float(x) for x in line.split()[:6]])
    a = np.array(rows)
    if np.any(np.diff(a[:, 0]) <= 0):
        print("WARNING: time is not strictly increasing in %s" % path)
    return a


def upward_zero_crossings(t, y):
    out = []
    for i in range(len(y) - 1):
        if y[i] < 0.0 <= y[i + 1]:
            out.append(t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))
    return np.array(out)


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    ref_path, test_path = sys.argv[1], sys.argv[2]
    t0, t1 = float(sys.argv[3]), float(sys.argv[4])
    dt = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0025

    ref, tst = load(ref_path), load(test_path)
    kr = np.round(ref[:, 0] / dt).astype(np.int64)
    kt = np.round(tst[:, 0] / dt).astype(np.int64)
    common, ir, it = np.intersect1d(kr, kt, return_indices=True)
    t = common * dt
    sel = (t >= t0 - 1e-9) & (t <= t1 + 1e-9)
    t, ir, it = t[sel], ir[sel], it[sel]
    cdr, cdt = ref[ir, 2], tst[it, 2]
    clr, clt = ref[ir, 3], tst[it, 3]
    print("samples: reference %d, test %d, joined in [%g, %g]: %d" % (len(ref), len(tst), t0, t1, len(t)))
    if len(t) == 0:
        sys.exit("no common samples")
    print("first joined time %.4f, last %.4f" % (t[0], t[-1]))
    print("reference Cl rms about its mean in the window: %.5f" % np.std(clr))
    print()
    print("%8s %10s %10s %10s %10s %10s %10s" % ("t", "Cd_ref", "Cd_test", "dCd", "Cl_ref", "Cl_test", "dCl"))
    last = -1
    for i in range(len(t)):
        k = int(np.floor(t[i] - t0 + 1e-9))
        if k != last:
            last = k
            print("%8.4f %10.5f %10.5f %10.5f %10.5f %10.5f %10.5f"
                  % (t[i], cdr[i], cdt[i], cdt[i] - cdr[i], clr[i], clt[i], clt[i] - clr[i]))
    print()
    for a, b in ((t0, t0 + 2.0), (t0 + 2.0, t0 + 10.0), (t0 + 10.0, t1)):
        m = (t >= a) & (t <= b)
        if m.sum() == 0:
            continue
        print("segment [%g, %g]: n=%d  rms dCd = %.5f  rms dCl = %.5f  max|dCl| = %.5f"
              % (a, b, m.sum(), np.sqrt(np.mean((cdt[m] - cdr[m]) ** 2)),
                 np.sqrt(np.mean((clt[m] - clr[m]) ** 2)), np.max(np.abs(clt[m] - clr[m]))))
    print()
    zr, zt = upward_zero_crossings(t, clr), upward_zero_crossings(t, clt)
    n = min(len(zr), len(zt))
    print("upward Cl zero crossings (ref, test, test-ref):")
    for i in range(n):
        print("  %9.4f %9.4f %+9.4f" % (zr[i], zt[i], zt[i] - zr[i]))
    if len(zr) != len(zt):
        print("  (counts differ: ref %d, test %d)" % (len(zr), len(zt)))


if __name__ == "__main__":
    main()
