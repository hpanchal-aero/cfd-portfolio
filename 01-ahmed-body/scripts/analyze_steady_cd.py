#!/usr/bin/env python3
"""
Extract Cd/Cl history for a steady-state Ahmed body case, handling
multi-stage forceCoeffs output (e.g. a run resumed partway through due
to a controlDict fix, as with the 0deg case's 0-1000 / 1000-2000 split).

Concatenates all postProcessing/forces/*/forceCoeffs.dat files, sorts
by iteration, and drops duplicate iteration numbers (keeping the LATER
stage's value, consistent with how OpenFOAM restarts overwrite from the
resume point forward).

Reports:
  - full concatenated history stats
  - windowed sub-means to check for a stationary mean (as done for the
    25deg case)
  - FFT of the (iteration-indexed, uniformly-sampled by construction --
    steady SIMPLEC iterations are integer-spaced) Cd signal, to check
    for a limit cycle vs genuine convergence/monotonic drift

Usage:
    python3 analyze_steady_cd.py <case_dir> [--window-start N] [--window-end N]

Example:
    python3 analyze_steady_cd.py \
        ~/cfd-portfolio/01-ahmed-body/cases/slant00_re4.18M_symtest \
        --window-start 1000 --window-end 2000
"""

import sys
import glob
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_forcecoeffs(case_dir):
    pattern = os.path.join(case_dir, "postProcessing", "forces", "*", "forceCoeffs.dat")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No forceCoeffs.dat files found under {pattern}")

    frames = []
    for f in files:
        df = pd.read_csv(f, comment="#", sep=r"\s+", header=None,
                          names=["Time", "Cm", "Cd", "Cl", "Cl_f", "Cl_r"])

        # Drop rows with any NaN values -- observed cause: a power-cut
        # interruption during an active write truncates the file's
        # final line mid-record, producing a partially or fully NaN
        # row after parsing. These rows carry no valid data and, being
        # at a restart boundary, are effectively duplicated by valid
        # data from the next file's early rows after resume.
        n_before = len(df)
        df = df.dropna()
        n_dropped = n_before - len(df)
        if n_dropped > 0:
            print(f"  {f}: dropped {n_dropped} NaN row(s) "
                  f"(likely truncated write from an interruption)")

        frames.append(df)
        print(f"Loaded {f}: {len(df)} rows, iteration range "
              f"{df['Time'].min():.0f}-{df['Time'].max():.0f}")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("Time", kind="mergesort")
    n_before = len(combined)
    combined = combined.drop_duplicates(subset="Time", keep="last")
    n_after = len(combined)
    if n_before != n_after:
        print(f"Dropped {n_before - n_after} duplicate iteration(s) at restart boundary.")

    combined = combined.reset_index(drop=True)
    return combined


def windowed_analysis(df, window_start, window_end, n_windows=5):
    window = df[(df["Time"] >= window_start) & (df["Time"] <= window_end)]
    if len(window) == 0:
        raise RuntimeError(f"No data in window [{window_start}, {window_end}]")

    print(f"\nWindow: iterations {window_start}-{window_end}, {len(window)} rows")
    print(f"Cd mean = {window['Cd'].mean():.6f}, std = {window['Cd'].std(ddof=1):.6f}")
    print(f"Cl mean = {window['Cl'].mean():.6f}, std = {window['Cl'].std(ddof=1):.6f}")

    edges = np.linspace(window_start, window_end, n_windows + 1)
    print(f"\nSub-window means ({n_windows} equal windows):")
    sub_means = []
    for i in range(n_windows):
        lo, hi = edges[i], edges[i + 1]
        sub = window[(window["Time"] >= lo) & (window["Time"] < hi if i < n_windows - 1 else window["Time"] <= hi)]
        m = sub["Cd"].mean()
        sub_means.append(m)
        print(f"  [{lo:.0f}, {hi:.0f}]: Cd mean = {m:.6f} (n={len(sub)})")

    spread = max(sub_means) - min(sub_means)
    print(f"Sub-window mean spread: {spread:.6f} ({100*spread/window['Cd'].mean():.2f}% of overall mean)")

    return window


def fft_analysis(window, out_png):
    cd = window["Cd"].to_numpy()
    t = window["Time"].to_numpy()

    dt = np.median(np.diff(t))
    n = len(cd)

    # Detrend by full linear fit, NOT just mean-subtraction. A window
    # with residual linear drift (as sub-window means often show)
    # leaks low-frequency power into the FFT that can alias to a
    # spurious "period" tracking the window length itself -- this
    # exact artifact was observed when this function used mean-only
    # detrending (see project log: 0deg case, 1200-2000 window
    # falsely reported period=200.25 on an 800-iteration window,
    # 800/4=200). Matches the method in sweep_steady_windows.py.
    slope, intercept = np.polyfit(t, cd, 1)
    cd_detrended = cd - (slope * t + intercept)

    fft_vals = np.fft.rfft(cd_detrended)
    freqs = np.fft.rfftfreq(n, d=dt)
    power = np.abs(fft_vals) ** 2

    if len(power) > 1:
        # Report top 5 peaks, not just the single strongest, since a
        # signal can have genuine multi-timescale structure (e.g. a
        # fast carrier oscillation with a slower amplitude-modulation
        # envelope) -- picking only the single dominant peak can hide
        # this and make a real fast oscillation look "wrong" if a
        # slower envelope happens to carry more power in a given window.
        nonzero_power = power[1:]
        nonzero_freqs = freqs[1:]
        top_n = min(5, len(nonzero_power))
        top_indices = np.argsort(nonzero_power)[::-1][:top_n]

        background_power = np.median(nonzero_power)

        trend_total = slope * (t[-1] - t[0])
        amplitude = cd.max() - cd.min()
        trend_fraction = 100 * abs(trend_total) / amplitude if amplitude > 0 else float("nan")

        print(f"\nLinear trend across window: {trend_total:.6f} "
              f"({trend_fraction:.1f}% of peak-to-peak amplitude)")
        print(f"\nTop {top_n} spectral peaks (linear-detrended):")
        print(f"{'Rank':>4} | {'Freq (cyc/iter)':>16} | {'Period (iter)':>14} | "
              f"{'Power':>12} | {'Power/background':>16}")
        for rank, idx in enumerate(top_indices, 1):
            f = nonzero_freqs[idx]
            p = nonzero_power[idx]
            period = 1.0 / f if f > 0 else float("inf")
            ratio = p / background_power if background_power > 0 else float("inf")
            flag = ""
            for denom in (1, 2, 3, 4, 5, 6):
                frac = len(cd) / denom * dt
                if period != float("inf") and abs(period - frac) / frac < 0.05:
                    flag = f"  (near window_length/{denom}={frac:.1f} -- check for artifact)"
                    break
            print(f"{rank:>4} | {f:>16.6f} | {period:>14.2f} | "
                  f"{p:>12.4e} | {ratio:>16.1f}{flag}")
    else:
        print("\nFFT: insufficient data for meaningful analysis")

    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    axes[0].plot(t, cd, lw=0.8)
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Cd")
    axes[0].set_title("Cd history (steady SIMPLEC)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(freqs[1:], power[1:], lw=0.8)
    axes[1].set_xlabel("Frequency (cycles/iteration)")
    axes[1].set_ylabel("Power")
    axes[1].set_title("FFT of detrended Cd signal")
    axes[1].set_yscale("log")
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"\nSaved plot: {out_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--window-start", type=float, default=1000)
    parser.add_argument("--window-end", type=float, default=2000)
    parser.add_argument("--out-png", default="steady_cd_fft.png")
    args = parser.parse_args()

    df = load_forcecoeffs(args.case_dir)
    print(f"\nTotal rows after cleanup: {len(df)}")
    print(f"Full range: iterations {df['Time'].min():.0f}-{df['Time'].max():.0f}")

    window = windowed_analysis(df, args.window_start, args.window_end)
    fft_analysis(window, args.out_png)


if __name__ == "__main__":
    main()
