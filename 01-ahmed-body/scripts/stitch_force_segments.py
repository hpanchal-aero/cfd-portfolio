#!/usr/bin/env python3
"""
Stitch the restart segments of an OpenFOAM forceCoeffs record into one
time series and report its integrity.

Segments are read from
    CASE/postProcessing/<object>/<start>/<file>
(default object 'forces', file 'forceCoeffs.dat'), sorted by the numeric
start directory. Rule: later segments win on overlaps -- each earlier segment
is cut at the first time of the next segment (rows with t < that time are
kept); the last segment is kept in full.

Optional --drop-time T (repeatable) removes the row whose time equals T
(within --tol). It exists for startup outliers; every dropped row is printed.
Raw files are never modified.

Reported: rows per segment, rows after stitching, time range, strict
monotonicity, duplicate times, NaN count, and for every seam the last kept
time, the first time of the next segment, and the maximum absolute difference
between overlapping rows (rows of the earlier segment at t >= the later
segment's first time, compared with the later segment's row at the same time).

Usage:
    stitch_force_segments.py --case CASE_DIR [--object forces]
        [--file forceCoeffs.dat] [--drop-time 2.63158e-05] [--out OUT.csv]
"""
import argparse
import glob
import os
import sys

import numpy as np


def read_segment(path):
    names, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                tok = line[1:].split()
                if tok and tok[0] == "Time":
                    names = tok
                continue
            if line.strip():
                rows.append([float(x) for x in line.split()])
    if names is None:
        sys.exit(f"{path}: no '# Time ...' column header found")
    arr = np.array(rows)
    if arr.ndim != 2 or arr.shape[1] != len(names):
        sys.exit(f"{path}: {arr.shape} data does not match {len(names)} columns")
    return names, arr


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True)
    ap.add_argument("--object", default="forces")
    ap.add_argument("--file", default="forceCoeffs.dat")
    ap.add_argument("--drop-time", type=float, action="append", default=[])
    ap.add_argument("--tol", type=float, default=1e-10)
    ap.add_argument("--out")
    a = ap.parse_args()

    pattern = os.path.join(a.case, "postProcessing", a.object, "*", a.file)
    found = []
    for p in glob.glob(pattern):
        try:
            found.append((float(os.path.basename(os.path.dirname(p))), p))
        except ValueError:
            print(f"skipping non-numeric segment directory: {p}")
    found.sort()
    if not found:
        sys.exit(f"no segments found for {pattern}")

    segs = []
    for start, p in found:
        names, arr = read_segment(p)
        segs.append((start, p, names, arr))
        print(f"segment {start:g}: {arr.shape[0]} rows, t {arr[0,0]:.6g} .. {arr[-1,0]:.6g}")
    names = segs[0][2]
    if any(s[2] != names for s in segs):
        sys.exit("column headers differ between segments")

    kept = []
    for i, (start, p, _, arr) in enumerate(segs):
        if i + 1 < len(segs):
            nxt = segs[i + 1][3]
            cut = nxt[0, 0]
            keep = arr[:, 0] < cut
            overlap = arr[~keep]
            later = {float(r[0]): r for r in nxt}
            diffs, missing = [], 0
            for r in overlap:
                m = later.get(float(r[0]))
                if m is None:
                    missing += 1
                else:
                    diffs.append(np.abs(r - m).max())
            md = max(diffs) if diffs else float("nan")
            last_kept = arr[keep][-1, 0] if keep.any() else float("nan")
            print(f"seam {start:g} -> {segs[i+1][0]:g}: last kept t {last_kept:.9g}, "
                  f"next first t {cut:.9g}, overlap rows {len(overlap)}, "
                  f"max |diff| {md:.3g}, overlap rows missing in later segment {missing}")
            arr = arr[keep]
        kept.append(arr)
    out = np.vstack(kept)

    for t in a.drop_time:
        hit = np.abs(out[:, 0] - t) <= a.tol
        n = int(hit.sum())
        if n:
            print(f"dropped {n} row(s) at t = {t:g}: " +
                  "; ".join(f"{nm} {v:.6g}" for nm, v in zip(names, out[hit][0])))
        else:
            print(f"WARNING: --drop-time {t:g} matched no row")
        out = out[~hit]

    t = out[:, 0]
    print(f"stitched rows: {len(out)}   t = {t[0]:.6g} .. {t[-1]:.6g}")
    print(f"strictly increasing: {bool(np.all(np.diff(t) > 0))}   "
          f"duplicate times: {len(t) - len(np.unique(t))}   NaN values: {int(np.isnan(out).sum())}")
    if a.out:
        np.savetxt(a.out, out, delimiter=",", header=",".join(names), comments="", fmt="%.10g")
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
