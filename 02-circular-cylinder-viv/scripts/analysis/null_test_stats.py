#!/usr/bin/env python3
"""null_test_stats.py -- acceptance statistics of the moving-mesh null test.

Usage:  null_test_stats.py <ref.dat> <test.dat> <t0> <t1> [dt]

Compares a spring-mounted (nearly fixed) moving-mesh run with the fixed-cylinder reference over
the window [t0, t1] using criteria set BEFORE these statistics were computed (2026-10-22):
  1. |delta mean Cd| / mean Cd_ref           <= TOL_CD_MEAN  percent
  2. |delta Cl rms| / Cl rms_ref             <= TOL_CL_RMS   percent   (rms about the mean)
  3. every upward Cl zero crossing in the window shifted by <= TOL_PHASE time units
Read-only; writes nothing.  Columns of forceCoeffs.dat: Time Cm Cd Cl Cl(f) Cl(r).
"""
import sys
import numpy as np

TOL_CD_MEAN = 0.5
TOL_CL_RMS = 2.0
TOL_PHASE = 0.05


def load(path):
    return np.loadtxt(path)


def crossings(t, y):
    out = []
    for i in range(len(y) - 1):
        if y[i] < 0.0 <= y[i + 1]:
            out.append(t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))
    return np.array(out)


def main():
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    ref, tst = load(sys.argv[1]), load(sys.argv[2])
    t0, t1 = float(sys.argv[3]), float(sys.argv[4])
    dt = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0025

    kr = np.round(ref[:, 0] / dt).astype(np.int64)
    kt = np.round(tst[:, 0] / dt).astype(np.int64)
    common, ir, it = np.intersect1d(kr, kt, return_indices=True)
    t = common * dt
    m = (t >= t0 - 1e-9) & (t <= t1 + 1e-9)
    t, ir, it = t[m], ir[m], it[m]
    if len(t) == 0:
        sys.exit("no common samples in the window")
    cdr, cdt = ref[ir, 2], tst[it, 2]
    clr, clt = ref[ir, 3], tst[it, 3]
    print("window [%g, %g], %d joined samples" % (t0, t1, len(t)))

    ok = True
    d_cd = 100.0 * (np.mean(cdt) - np.mean(cdr)) / np.mean(cdr)
    p1 = abs(d_cd) <= TOL_CD_MEAN
    print("1. mean Cd: ref %.5f  test %.5f  diff %+.3f %%  (tol %.1f %%)  %s"
          % (np.mean(cdr), np.mean(cdt), d_cd, TOL_CD_MEAN, "PASS" if p1 else "FAIL"))

    rr, rt = np.std(clr), np.std(clt)
    d_cl = 100.0 * (rt - rr) / rr
    p2 = abs(d_cl) <= TOL_CL_RMS
    print("2. Cl rms:  ref %.5f  test %.5f  diff %+.3f %%  (tol %.1f %%)  %s"
          % (rr, rt, d_cl, TOL_CL_RMS, "PASS" if p2 else "FAIL"))

    zr, zt = crossings(t, clr), crossings(t, clt)
    if len(zr) != len(zt) or len(zr) == 0:
        p3 = False
        print("3. zero crossings: counts differ or none (ref %d, test %d)  FAIL" % (len(zr), len(zt)))
    else:
        d = zt - zr
        p3 = bool(np.all(np.abs(d) <= TOL_PHASE))
        print("3. upward Cl zero crossings (ref, test, shift):")
        for a, b in zip(zr, zt):
            print("     %9.4f %9.4f %+8.4f" % (a, b, b - a))
        print("   max |shift| %.4f  (tol %.2f)  %s" % (np.max(np.abs(d)), TOL_PHASE, "PASS" if p3 else "FAIL"))

    print("OVERALL: %s" % ("PASS" if (p1 and p2 and p3) else "FAIL"))


if __name__ == "__main__":
    main()
