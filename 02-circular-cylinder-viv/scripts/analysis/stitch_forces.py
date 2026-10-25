#!/usr/bin/env python3
"""Stitch the force records of a run that was interrupted and restarted from a saved time.

Usage: stitch_forces.py <case_dir> <restart_time>

Inputs : <case_dir>/postProcessing/forces/0/forceCoeffs.dat               first part (up to the interruption)
         <case_dir>/postProcessing/forces/<restart_time>/forceCoeffs.dat  restarted part
Output : <case_dir>/postProcessing/forces/stitched/forceCoeffs.dat
Rule   : rows of the first part with t < restart_time, then all rows of the restarted part.
         Lines of the first part that do not hold six numbers (the damaged last line after a crash)
         are dropped and counted. The two inputs are not modified.
Prints : integrity checks of the stitched record (rows, first and last time, time-step spacing,
         duplicates) and the comparison of the two parts where they overlap (the interval that the
         first part had already computed after the restart time), which measures what the restart changes.
"""
import sys
from pathlib import Path

import numpy as np

if len(sys.argv) != 3:
    sys.exit("usage: stitch_forces.py <case_dir> <restart_time>")
case = Path(sys.argv[1])
tr = float(sys.argv[2])
f0 = case / "postProcessing/forces/0/forceCoeffs.dat"
f1 = case / f"postProcessing/forces/{sys.argv[2]}/forceCoeffs.dat"
out = case / "postProcessing/forces/stitched/forceCoeffs.dat"
for f in (f0, f1):
    if not f.is_file():
        sys.exit(f"missing {f}")


def read(path):
    header, rows, dropped = [], [], 0
    for line in path.read_bytes().decode("latin-1").splitlines():
        if line.startswith("#"):
            header.append(line)
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            vals = [float(x) for x in parts]
        except ValueError:
            dropped += 1
            continue
        if len(vals) != 6:
            dropped += 1
            continue
        rows.append(vals)
    return header, np.array(rows), dropped


h0, r0, d0 = read(f0)
h1, r1, d1 = read(f1)
print(f"first part   : {len(r0)} rows, t = {r0[0, 0]:g} .. {r0[-1, 0]:g}, lines dropped {d0}")
print(f"restart part : {len(r1)} rows, t = {r1[0, 0]:g} .. {r1[-1, 0]:g}, lines dropped {d1}")

eps = 1e-6
a = r0[r0[:, 0] < tr - eps]
st = np.vstack([a, r1])
t = st[:, 0]
dts = np.diff(t)
dt = np.median(dts)
print(f"stitched     : {len(st)} rows, t = {t[0]:g} .. {t[-1]:g}")
print(f"time step    : median {dt:g}, max deviation {np.max(np.abs(dts - dt)):.2e}, "
      f"duplicates or reversals {int(np.sum(dts <= 0))}")

key0 = np.round(r0[:, 0] * 1e6).astype(np.int64)
key1 = np.round(r1[:, 0] * 1e6).astype(np.int64)
common, i0, i1 = np.intersect1d(key0, key1, return_indices=True)
if len(common) == 0:
    print("overlap      : none")
else:
    print(f"overlap      : {len(common)} rows, t = {r0[i0[0], 0]:g} .. {r0[i0[-1], 0]:g}")
    for name, c in (("Cd", 2), ("Cl", 3)):
        x0, x1 = r0[i0, c], r1[i1, c]
        d = x1 - x0
        if name == "Cd":
            scale = np.mean(np.abs(x0))
        else:
            scale = 0.5 * (x0.max() - x0.min())
        rms = np.sqrt(np.mean(d ** 2))
        print(f"  {name}: restart - first part, first 3 rows {d[:3]}, last row {d[-1]:.3e}")
        print(f"      max |diff| {np.max(np.abs(d)):.3e}   rms diff {rms:.3e}   scale {scale:.4f}"
              f"   rms/scale {rms / scale:.3e}   max/scale {np.max(np.abs(d)) / scale:.3e}")

out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as fh:
    for line in h0:
        fh.write(line + "\n")
    for row in st:
        fh.write(f"{row[0]:.10g}\t" + "\t".join(f"{v:.8e}" for v in row[1:]) + "\n")
print(f"written      : {out}")
