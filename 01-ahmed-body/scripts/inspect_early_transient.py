#!/usr/bin/env python3
"""
Quick inspection of Cd/Cl trajectory over whatever time range is
currently available -- for checking early-transient behavior before
a stationarity window is expected to exist yet. Not a stationarity
analysis; just shows the raw trend so far.

Usage:
    python3 inspect_early_transient.py <case_dir>
"""
import sys
import glob
import os
import pandas as pd
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
    case_dir = sys.argv[1]
    df = load_forcecoeffs(case_dir)

    print(f"Rows: {len(df)}, time range: {df['Time'].min():.6f} - {df['Time'].max():.6f} s")

    n_points = min(10, len(df))
    idxs = [int(i * (len(df) - 1) / (n_points - 1)) for i in range(n_points)]
    print(f"\n{'Time':>10} | {'Cd':>10} | {'Cl':>10}")
    for i in idxs:
        row = df.iloc[i]
        print(f"{row['Time']:>10.6f} | {row['Cd']:>10.6f} | {row['Cl']:>10.6f}")

    q = len(df) // 4
    first_q_cd = df["Cd"].iloc[:q].mean()
    last_q_cd = df["Cd"].iloc[-q:].mean()
    pct_change = 100 * (last_q_cd - first_q_cd) / first_q_cd
    print(f"\nCd first-quarter mean: {first_q_cd:.6f}")
    print(f"Cd last-quarter mean:  {last_q_cd:.6f}")
    print(f"Change: {pct_change:+.2f}%")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Time"], df["Cd"], label="Cd", lw=0.8)
    ax.plot(df["Time"], df["Cl"], label="Cl", lw=0.8)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Coefficient")
    ax.set_title("Early transient trajectory (raw, not stationarity-verified)")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("early_transient_check.png", dpi=150)
    print("\nSaved: early_transient_check.png")


if __name__ == "__main__":
    main()
