#!/usr/bin/env python3
"""
Lomb-Scargle spectra of the force coefficients and a wake-probe record, and the
pre-stated corroboration criterion (35 deg analysis).

Signals: Cd and Cl (from the stitched CSV written by stitch_force_segments.py)
and p, Ux, Uy, Uz at the wake probe (CASE/postProcessing/wakeProbes/<start>/p and
U; restart segments are stitched with later segments winning, as in the force
record). Each window [a, b] (inclusive) is processed separately:
    1. a straight line (least squares in t) is removed from the signal;
    2. the Lomb-Scargle power (valid for non-uniform sampling) is evaluated on
       the grid fmin..fmax with step df;
    3. peaks are the local maxima of the spectrum inside the band, ranked by
       power (the published ranks, e.g. Ux 57.5 Hz #3 in window 0.14-0.30,
       require ranking inside the band; --rank-all ranks over the whole grid);
    4. x = peak power / median power over the band (default 10-100 Hz).
x is a rough indicator, not a significance test.

Criterion (as stated in the README): a Strouhal number is reported only if Cd and
at least one probe signal each have a top-3 peak with x >= 5 within +-10 % of the
same frequency, in every window. The script prints the matches per window and the
verdict; it does not alter the thresholds.

Usage:
    spectral_probe_check.py --force-csv stitched.csv --probe-case CASE_DIR
        --windows 0.18:0.30 0.14:0.30 [--fmin 0.5 --fmax 150 --df 0.5]
        [--band 10 100] [--top 5] [--threshold 5]
"""
import argparse
import glob
import os
import re
import sys

import numpy as np
from scipy.signal import find_peaks, lombscargle

EPS = 1e-12


def read_probe(case, obj, name):
    segs = []
    for p in glob.glob(os.path.join(case, "postProcessing", obj, "*", name)):
        try:
            segs.append((float(os.path.basename(os.path.dirname(p))), p))
        except ValueError:
            pass
    segs.sort()
    if not segs:
        sys.exit(f"no probe segments for {name} under {case}/postProcessing/{obj}")
    arrs = []
    for _, p in segs:
        rows = []
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                toks = [v for v in re.split(r"[\s()]+", line.strip()) if v]
                rows.append([float(v) for v in toks])
        arrs.append(np.array(rows))
    out = []
    for i, arr in enumerate(arrs):
        if i + 1 < len(arrs):
            seam = (arr[arr[:, 0] < arrs[i + 1][0, 0]][-1, 0], arrs[i + 1][0, 0], arrs[i + 1][1, 0])
            print(f"probe {name} seam {segs[i][0]:g} -> {segs[i+1][0]:g}: "
                  f"{seam[0]:.6g} -> {seam[1]:.6g} -> {seam[2]:.6g}")
            arr = arr[arr[:, 0] < arrs[i + 1][0, 0]]
        out.append(arr)
    return np.vstack(out)


def spectrum(t, y, freqs):
    tt = t - t[0]
    r = y - np.polyval(np.polyfit(tt, y, 1), tt)
    r = r - r.mean()
    return lombscargle(tt, r, 2.0 * np.pi * freqs)


def peaks(freqs, power, band, rank_in_band=True):
    idx, _ = find_peaks(power)
    if rank_in_band:
        idx = idx[(freqs[idx] >= band[0]) & (freqs[idx] <= band[1])]
    med = np.median(power[(freqs >= band[0]) & (freqs <= band[1])])
    order = idx[np.argsort(power[idx])[::-1]]
    return [(freqs[i], power[i] / med) for i in order]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force-csv", required=True)
    ap.add_argument("--probe-case", required=True)
    ap.add_argument("--probe-object", default="wakeProbes")
    ap.add_argument("--windows", nargs="+", required=True)
    ap.add_argument("--fmin", type=float, default=0.5)
    ap.add_argument("--fmax", type=float, default=150.0)
    ap.add_argument("--df", type=float, default=0.5)
    ap.add_argument("--band", type=float, nargs=2, default=[10.0, 100.0])
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=5.0)
    ap.add_argument("--rank-all", action="store_true",
                    help="rank peaks over the whole grid instead of inside the band")
    a = ap.parse_args()

    with open(a.force_csv, encoding="utf-8") as fh:
        names = fh.readline().strip().split(",")
    f = np.loadtxt(a.force_csv, delimiter=",", skiprows=1)
    ci = {n: i for i, n in enumerate(names)}
    sig = {"Cd": (f[:, 0], f[:, ci["Cd"]]), "Cl": (f[:, 0], f[:, ci["Cl"]])}
    pr = read_probe(a.probe_case, a.probe_object, "p")
    ur = read_probe(a.probe_case, a.probe_object, "U")
    sig["p"] = (pr[:, 0], pr[:, 1])
    for k, n in enumerate(("Ux", "Uy", "Uz")):
        sig[n] = (ur[:, 0], ur[:, 1 + k])
    freqs = np.arange(a.fmin, a.fmax + a.df / 2, a.df)

    matches_by_window = {}
    for spec in a.windows:
        t0, t1 = (float(x) for x in spec.split(":"))
        print(f"\n=== window {spec}  (grid {a.fmin:g}-{a.fmax:g} Hz, step {a.df:g}, band {a.band[0]:g}-{a.band[1]:g} Hz)")
        top3 = {}
        for name, (t, y) in sig.items():
            m = (t >= t0 - EPS) & (t <= t1 + EPS)
            pk = peaks(freqs, spectrum(t[m], y[m], freqs), a.band, rank_in_band=not a.rank_all)
            top3[name] = [(fr, x) for fr, x in pk[:3] if x >= a.threshold]
            print(f"{name:>3} n={int(m.sum()):6d}  " +
                  "  ".join(f"#{i+1} {fr:5.1f} Hz x{x:5.1f}" for i, (fr, x) in enumerate(pk[:a.top])))
        matches = []
        for fc, xc in top3["Cd"]:
            for probe in ("p", "Ux", "Uy", "Uz"):
                for fp, xp in top3[probe]:
                    if abs(fp - fc) <= 0.10 * fc:
                        matches.append((fc, probe, fp))
        matches_by_window[spec] = matches
        print("criterion matches (Cd top-3 x>=%g vs probe top-3 x>=%g, +-10%%): %s" %
              (a.threshold, a.threshold,
               "; ".join(f"Cd {fc:.1f} Hz ~ {pn} {fp:.1f} Hz" for fc, pn, fp in matches) or "none"))

    met = all(matches_by_window[s] for s in a.windows)
    print("\ncorroboration criterion met in every window:", met)


if __name__ == "__main__":
    main()
