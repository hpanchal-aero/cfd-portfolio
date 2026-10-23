#!/usr/bin/env python3
"""body_motion.py -- body motion and force balance of a spring-mounted moving-mesh run.

Usage:  body_motion.py <case_dir> <t0> <t1>

Reads   <case_dir>/log.foamRun   (6-DoF report: "Centre of mass: (x y z)", last report of each step)
        <case_dir>/postProcessing/forces/<startTime>/forceCoeffs.dat  (Time Cm Cd Cl Cl(f) Cl(r))
        <case_dir>/moving.params  (line "k <stiffness>")
Prints
  1. all local maxima of y(t) over the whole run (growth / saturation of the cross-flow response),
  2. in the window [t0, t1]: upward zero crossings of y - mean(y), the body period and frequency taken
     over WHOLE periods (first to last crossing), y amplitude (max-min)/2, mean x and mean y,
  3. over the same whole periods: mean Cd, mean Cl, Cl rms, Cl zero-crossing frequency and the force
     balance  k*mean(x) = mean(Cd)*0.5*Aref  (rho = U = D = 1, Aref = 0.1) with its relative error;
     criterion (set before running): |relative error| <= 3 %.
Read-only; writes nothing.
"""
import glob
import re
import sys
import numpy as np

AREF = 0.1
TOL_BAL = 3.0  # percent


def read_state(log):
    rc = re.compile(r"Centre of mass: \((\S+) (\S+) (\S+)\)")
    t = None
    d = {}
    for line in open(log):
        if line.startswith("Time = "):
            t = float(line.split()[2].rstrip("s"))
        elif "Centre of mass:" in line and t is not None:
            m = rc.search(line)
            if m:
                d[t] = (float(m.group(1)), float(m.group(2)))
    ts = np.array(sorted(d))
    xy = np.array([d[k] for k in ts])
    return ts, xy[:, 0], xy[:, 1]


def upward_crossings(t, y):
    out = []
    for i in range(len(y) - 1):
        if y[i] < 0.0 <= y[i + 1]:
            out.append(t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))
    return np.array(out)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    case = sys.argv[1].rstrip("/")
    t0, t1 = float(sys.argv[2]), float(sys.argv[3])

    t, x, y = read_state(case + "/log.foamRun")
    print("states read: %d steps, t = %.4f .. %.4f" % (len(t), t[0], t[-1]))

    k = None
    for line in open(case + "/moving.params"):
        if line.startswith("k "):
            k = float(line.split()[1])
    if k is None:
        sys.exit("no stiffness k in moving.params")
    print("stiffness k = %g" % k)

    print("\nlocal maxima of y (time, y):")
    peaks = [i for i in range(1, len(y) - 1) if y[i] > y[i - 1] and y[i] >= y[i + 1] and y[i] > 0.02]
    for i in peaks:
        print("  %9.4f  %+.4f" % (t[i], y[i]))

    m = (t >= t0) & (t <= t1)
    tw, xw, yw = t[m], x[m], y[m]
    zc = upward_crossings(tw, yw - np.mean(yw))
    print("\nwindow [%g, %g]: %d upward y crossings" % (t0, t1, len(zc)))
    if len(zc) < 2:
        sys.exit("need at least two crossings in the window")
    for z in zc:
        print("   %9.4f" % z)
    a, b = zc[0], zc[-1]
    n_per = len(zc) - 1
    period = (b - a) / n_per
    print("whole periods: %d over [%.4f, %.4f]; body period %.4f, frequency %.5f" % (n_per, a, b, period, 1.0 / period))
    mw = (t >= a) & (t <= b)
    print("y amplitude (max-min)/2 = %.4f, mean y = %+.5f, mean x = %.5f, x peak-to-peak = %.4f"
          % ((yw[(tw >= a) & (tw <= b)].max() - yw[(tw >= a) & (tw <= b)].min()) / 2.0,
             np.mean(y[mw]), np.mean(x[mw]), x[mw].max() - x[mw].min()))

    start = re.search(r"^startTime\s+(\S+);", open(case + "/system/controlDict").read(), re.M).group(1)
    f = glob.glob("%s/postProcessing/forces/*/forceCoeffs.dat" % case)
    if len(f) != 1:
        sys.exit("expected one forceCoeffs.dat, found %d" % len(f))
    fc = np.loadtxt(f[0])
    mf = (fc[:, 0] >= a) & (fc[:, 0] <= b)
    tf, cd, cl = fc[mf, 0], fc[mf, 2], fc[mf, 3]
    zl = upward_crossings(tf, cl - np.mean(cl))
    print("\nforces over the same whole periods (%d samples):" % mf.sum())
    print("  mean Cd = %.5f, mean Cl = %+.5f, Cl rms about mean = %.5f" % (np.mean(cd), np.mean(cl), np.std(cl)))
    if len(zl) >= 2:
        print("  Cl upward crossings: %d, mean period %.4f, frequency %.5f" % (len(zl), (zl[-1] - zl[0]) / (len(zl) - 1), (len(zl) - 1) / (zl[-1] - zl[0])))
    bal_x = k * np.mean(x[mw]) / (0.5 * AREF)
    err = 100.0 * (bal_x - np.mean(cd)) / np.mean(cd)
    print("\nforce balance in x:  k*mean(x)/(0.5*Aref) = %.5f  vs mean Cd = %.5f  ->  %+.2f %%  (tol %.0f %%)  %s"
          % (bal_x, np.mean(cd), err, TOL_BAL, "PASS" if abs(err) <= TOL_BAL else "FAIL"))
    bal_y = k * np.mean(y[mw]) / (0.5 * AREF)
    print("force balance in y:  k*mean(y)/(0.5*Aref) = %+.5f  vs mean Cl = %+.5f  (difference %+.5f, information only)"
          % (bal_y, np.mean(cl), bal_y - np.mean(cl)))
    print("(startTime of this run: %s)" % start)


if __name__ == "__main__":
    main()
