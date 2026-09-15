#!/usr/bin/env python3
"""
Sliding-window sweep over the steady-case Cd(iteration) signal to find
where the signal becomes stationary, and to distinguish a genuine
oscillation period from an FFT artifact tracking window length.

For each (window_length, start) combination, reports:
  - Cd mean and linear trend (slope) within the window -- a large
    trend relative to the oscillation amplitude indicates the window
    still contains non-stationary drift, not just a stable limit cycle.
  - FFT dominant period and peak/background power ratio.
  - A flag if the reported period is suspiciously close to a simple
    fraction of the window length itself (a known artifact pattern:
    e.g. period ~= window_length/2, /4, /5), since that pattern has
    already been observed to be spurious in this project.

This does NOT replace manual inspection of the plots -- it is meant to
narrow down candidate stationary windows for closer, single-window
analysis via analyze_steady_cd.py.

Usage:
    python3 sweep_steady_windows.py <case_dir> \
        --window-lengths 200 300 500 \
        --start-min 1000 --start-max 1500 --start-step 100
"""

import argparse
import glob
import os
import numpy as np
import pandas as pd


def load_forcecoeffs(case_dir):
    pattern = os.path.join(case_dir, "postProcessing", "forces", "*", "forceCoeffs.dat")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No forceCoeffs.dat files found under {pattern}")

    frames = []
    for f in files:
        df = pd.read_csv(
            f, comment="#", sep=r"\s+", header=None,
            names=["Time", "Cm", "Cd", "Cl", "Cl_f", "Cl_r"],
        )
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("Time", kind="mergesort")
    combined = combined.drop_duplicates(subset="Time", keep="last")
    combined = combined.reset_index(drop=True)
    return combined


def analyze_window(df, start, length):
    end = start + length
    window = df[(df["Time"] >= start) & (df["Time"] < end)]
    if len(window) < 10:
        return None

    t = window["Time"].to_numpy()
    cd = window["Cd"].to_numpy()

    slope, intercept = np.polyfit(t, cd, 1)
    trend_total = slope * length
    amplitude = cd.max() - cd.min()
    trend_fraction = abs(trend_total) / amplitude if amplitude > 0 else float("nan")

    cd_detrended = cd - (slope * t + intercept)
    dt = np.median(np.diff(t))
    n = len(cd)
    fft_vals = np.fft.rfft(cd_detrended)
    freqs = np.fft.rfftfreq(n, d=dt)
    power = np.abs(fft_vals) ** 2

    if len(power) <= 1:
        return None

    peak_idx = np.argmax(power[1:]) + 1
    peak_freq = freqs[peak_idx]
    period = 1.0 / peak_freq if peak_freq > 0 else float("inf")
    background_power = np.median(power[1:])
    ratio = power[peak_idx] / background_power if background_power > 0 else float("inf")

    suspicious = False
    for denom in (1, 2, 3, 4, 5, 6):
        frac = length / denom
        if abs(period - frac) / frac < 0.05:
            suspicious = True
            break

    return {
        "start": start,
        "end": end,
        "length": length,
        "mean": cd.mean(),
        "trend_fraction_pct": 100 * trend_fraction,
        "period": period,
        "power_ratio": ratio,
        "suspicious": suspicious,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--window-lengths", type=int, nargs="+", default=[200, 300, 500])
    parser.add_argument("--start-min", type=int, default=1000)
    parser.add_argument("--start-max", type=int, default=1500)
    parser.add_argument("--start-step", type=int, default=100)
    args = parser.parse_args()

    df = load_forcecoeffs(args.case_dir)
    max_time = df["Time"].max()

    print(f"{'Length':>7} | {'Start':>6} | {'End':>6} | {'Mean':>9} | "
          f"{'Trend%':>8} | {'Period':>8} | {'PowerRatio':>12} | Flag")
    print("-" * 80)

    for length in args.window_lengths:
        start = args.start_min
        while start <= args.start_max and start + length <= max_time:
            r = analyze_window(df, start, length)
            if r is not None:
                flag = "WINDOW-LENGTH ARTIFACT?" if r["suspicious"] else ""
                print(f"{r['length']:>7} | {r['start']:>6} | {r['end']:>6} | "
                      f"{r['mean']:>9.6f} | {r['trend_fraction_pct']:>7.1f}% | "
                      f"{r['period']:>8.2f} | {r['power_ratio']:>12.1f} | {flag}")
            start += args.start_step


if __name__ == "__main__":
    main()
