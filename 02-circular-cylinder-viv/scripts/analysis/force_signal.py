#!/usr/bin/env python3
"""force_signal.py -- statistics of a forceCoeffs.dat time series.

Columns of forceCoeffs.dat (OpenFOAM 11): Time Cm Cd Cl Cl(f) Cl(r)
D = 1 and U = 1 in all cases here, so frequency = Strouhal number.

Usage:
    /usr/bin/python3 force_signal.py <forceCoeffs.dat> [--t0 T0] [--t1 T1] [--tmin TMIN]
                                      [--fig out.png] [--json out.json]

Statistics are computed over a WHOLE NUMBER OF PERIODS inside [T0, T1] (from the first to the
last upward zero-crossing of Cl - mid-level), so that a partial cycle does not bias the means.
The per-cycle table covers the whole record from TMIN on.
"""
import argparse
import json
import sys

import numpy as np


def load(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            rows.append([float(x) for x in line.split()])
    return np.array(rows)


def upcrossings(t, y):
    """Times at which y crosses zero upwards (linear interpolation)."""
    i = np.where((y[:-1] < 0) & (y[1:] >= 0))[0]
    return t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i])


def fft_peak(t, y, fmin=0.05, fmax=0.5):
    """Frequency of the spectral peak in [fmin, fmax] (Hann window, zero padding,
    parabolic interpolation of the log-spectrum)."""
    dt = np.mean(np.diff(t))
    y = y - y.mean()
    w = np.hanning(len(y))
    n = 1 << int(np.ceil(np.log2(len(y) * 8)))
    spec = np.abs(np.fft.rfft(y * w, n))
    f = np.fft.rfftfreq(n, dt)
    band = (f >= fmin) & (f <= fmax)
    k = np.where(band)[0][np.argmax(spec[band])]
    kf = float(k)
    if 0 < k < len(spec) - 1:
        a, b, c = np.log(spec[k - 1:k + 2] + 1e-300)
        den = a - 2 * b + c
        if den != 0:
            kf = k + 0.5 * (a - c) / den
    return kf * (f[1] - f[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dat")
    ap.add_argument("--t0", type=float, default=None, help="window start (default: half of record)")
    ap.add_argument("--t1", type=float, default=None, help="window end (default: end of record)")
    ap.add_argument("--tmin", type=float, default=10.0, help="first time of the per-cycle table")
    ap.add_argument("--fig", default=None, help="save a Cl(t), Cd(t) figure to this file")
    ap.add_argument("--json", default=None, help="write the window metrics to this JSON file")
    args = ap.parse_args()

    a = load(args.dat)
    t, cd, cl = a[:, 0], a[:, 2], a[:, 3]
    dt = float(np.mean(np.diff(t)))
    if not np.allclose(np.diff(t), dt, rtol=1e-3):
        print("WARNING: time step is not uniform; FFT result is not reliable")
    t0 = args.t0 if args.t0 is not None else 0.5 * (t[0] + t[-1])
    t1 = args.t1 if args.t1 is not None else t[-1]
    m = (t >= t0) & (t <= t1)
    if m.sum() < 10:
        sys.exit("ERROR: fewer than 10 samples in the window")

    # --- window statistics over a whole number of periods -----------------------------------
    level = 0.5 * (cl[m].max() + cl[m].min())
    xw = upcrossings(t[m], cl[m] - level)
    if len(xw) < 3:
        sys.exit("ERROR: fewer than 3 up-crossings in the window: no periodic signal to analyse")
    ta, tb = xw[0], xw[-1]
    w = (t >= ta) & (t <= tb)
    tw, cdw, clw = t[w], cd[w], cl[w]
    per = np.diff(xw)
    st_zc = 1.0 / per.mean()
    st_fft = fft_peak(tw, clw)

    print(f"record : t = {t[0]:g} .. {t[-1]:g}, {len(t)} samples, dt = {dt:.6g}")
    print(f"request: t = {t0:g} .. {t1:g}")
    print(f"window : t = {ta:.3f} .. {tb:.3f}  ({len(per)} whole periods, {tb - ta:.2f} time units)")
    print(f"Cd     : mean {cdw.mean():.5f}  std {cdw.std():.5f}  (max-min)/2 {(cdw.max() - cdw.min()) / 2:.5f}")
    print(f"Cl     : mean {clw.mean():+.5f}  rms {clw.std():.5f}  (max-min)/2 {(clw.max() - clw.min()) / 2:.5f}")
    print(f"periods: mean {per.mean():.4f}  std {per.std():.5f}  min {per.min():.4f}  max {per.max():.4f}")
    print(f"St     : zero-crossing {st_zc:.4f}   FFT {st_fft:.4f}")

    # --- per-cycle table over the record (shows onset and saturation) ------------------------
    xa = upcrossings(t, cl)
    xa = xa[xa >= args.tmin]
    print(f"per-cycle table from t = {args.tmin:g} (Cl up-crossings through 0):")
    print("     t_start   period   Cl_amp    Cd_mean")
    for p, q in zip(xa[:-1], xa[1:]):
        c = (t >= p) & (t < q)
        print(f"   {p:8.2f}  {q - p:7.4f}  {0.5 * (cl[c].max() - cl[c].min()):7.4f}   {cd[c].mean():8.5f}")

    if args.json:
        out = {"file": args.dat, "t_start": float(ta), "t_end": float(tb), "n_periods": int(len(per)),
               "St_zero_crossing": float(st_zc), "St_fft": float(st_fft),
               "Cd_mean": float(cdw.mean()), "Cd_std": float(cdw.std()),
               "Cl_rms": float(clw.std()), "Cl_amplitude": float(0.5 * (clw.max() - clw.min())),
               "period_mean": float(per.mean()), "period_std": float(per.std())}
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=2)
        print(f"json written: {args.json}")

    if args.fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        s = t >= 1.0          # drop the impulsive-start spike (first ~0.05 time units)
        fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
        ax[0].plot(t[s], cl[s], lw=0.8)
        ax[0].set_ylabel("Cl")
        ax[1].plot(t[s], cd[s], lw=0.8)
        ax[1].set_ylabel("Cd")
        ax[1].set_xlabel("t U / D")
        for axis in ax:
            axis.axvspan(ta, tb, color="0.9", zorder=0)
            axis.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.fig, dpi=150)
        print(f"figure written: {args.fig}")


if __name__ == "__main__":
    main()
