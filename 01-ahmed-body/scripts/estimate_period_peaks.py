#!/usr/bin/env python3
"""
Time-domain peak-to-peak period estimation for a transient Cd(t) signal,
for cases where too few cycles exist for a reliable FFT (matches the
25deg case's approach: "Time-domain peak-to-peak measurement (more
reliable than the FFT bin estimate, given the limited number of cycles
available)").

Finds local maxima (peaks) in Cd(t) within a specified window, reports
the time interval between consecutive peaks (= period estimate), and
the corresponding frequency and Strouhal number (using body height H,
per the literature convention verified for the 25deg case).

Usage:
    python3 estimate_period_peaks.py <case_dir> --window-start T0 --window-end T1
        [--min-prominence P] [--H 0.288] [--U 60]
"""
import argparse
import glob
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_forcecoeffs(case_dir):
    pattern = os.path.join(case_dir, "postProcessing", "forces", "*", "forceCoeffs.dat")
    files = sorted(glob.glob(pattern))
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
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("Time", kind="mergesort")
    combined = combined.drop_duplicates(subset="Time", keep="last")
    return combined.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--window-start", type=float, required=True)
    parser.add_argument("--window-end", type=float, required=True)
    parser.add_argument("--min-prominence", type=float, default=None,
                         help="Minimum peak prominence (Cd units). If not set, "
                              "defaults to 10% of the window's Cd std dev.")
    parser.add_argument("--H", type=float, default=0.288,
                         help="Body height [m], for Strouhal number (verified "
                              "convention: St = f*H/U, not L)")
    parser.add_argument("--U", type=float, default=60.0, help="Freestream velocity [m/s]")
    args = parser.parse_args()

    df = load_forcecoeffs(args.case_dir)
    window = df[(df["Time"] >= args.window_start) & (df["Time"] <= args.window_end)]

    if len(window) < 10:
        raise RuntimeError(f"Only {len(window)} rows in window -- too few to analyze.")

    t = window["Time"].to_numpy()
    cd = window["Cd"].to_numpy()

    prominence = args.min_prominence
    if prominence is None:
        prominence = 0.1 * cd.std()

    peak_indices, properties = find_peaks(cd, prominence=prominence)

    print(f"Window: t = {args.window_start}-{args.window_end} s, {len(window)} rows")
    print(f"Cd std in window: {cd.std():.6f}")
    print(f"Prominence threshold used: {prominence:.6f}")
    print(f"\nPeaks found: {len(peak_indices)}")

    if len(peak_indices) < 2:
        print("Fewer than 2 peaks found -- cannot estimate period from peak spacing. "
              "Consider lowering --min-prominence or extending the window.")
    else:
        peak_times = t[peak_indices]
        print(f"\nPeak times (s): {[f'{pt:.6f}' for pt in peak_times]}")

        periods = np.diff(peak_times)
        print(f"\nInter-peak periods (s): {[f'{p:.6f}' for p in periods]}")
        print(f"Mean period: {periods.mean():.6f} s (std {periods.std():.6f}, "
              f"CoV {100*periods.std()/periods.mean():.2f}%)")

        freq = 1.0 / periods.mean()
        St = freq * args.H / args.U
        print(f"\nCorresponding frequency: {freq:.4f} Hz")
        print(f"Strouhal number (H={args.H} m, U={args.U} m/s): St = {St:.4f}")

        if len(periods) < 3:
            print(f"\nCAUTION: only {len(periods)} period measurement(s) -- "
                  "this estimate is based on very few cycles and should be "
                  "treated as preliminary. More runtime recommended before "
                  "treating this as a settled result.")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(t, cd, lw=0.8, label="Cd")
    if len(peak_indices) > 0:
        ax.plot(t[peak_indices], cd[peak_indices], "rx", markersize=10, label="detected peaks")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Cd")
    ax.set_title(f"Peak detection, t={args.window_start}-{args.window_end}s")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("peak_detection_check.png", dpi=150)
    print("\nSaved: peak_detection_check.png")


if __name__ == "__main__":
    main()
