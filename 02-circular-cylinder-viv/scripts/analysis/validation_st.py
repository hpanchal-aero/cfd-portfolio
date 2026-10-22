#!/usr/bin/env python3
"""Strouhal-number validation of the fixed cylinder against Williamson (1989), at Re = 100 and 150.

Usage: validation_st.py [exploratory_dir]

Reference: C. H. K. Williamson, J. Fluid Mech. 206, 579-627 (1989), Eq. (6), p. 606:
    St = A/Re + B + C*Re,   A = -3.3265, B = 0.1816, C = 1.600e-4
a least-squares fit to experimental parallel-shedding data. The paper states the laminar shedding
regime as Re = 49 to 178 and, on p. 607, an average percentage error of the fit of 0.06 %.
U_ref = 0.06 % is that stated fit error. It is a lower bound for the reference uncertainty: it does
not contain the measurement uncertainty, which is not given in the parts of the paper that were read.

Rule (notes/02-validation-criteria.md): band = max(floor, U_num + U_ref), floor 2 % for St.
U_num = mesh term (medium -> fine) + time-step term (last halving) + domain term (D7b sum), all as in
verification_table.py. The compared value is the baseline configuration (medium mesh, dt = 0.0025,
baseline domain), the one whose differences define U_num.
Experiments are 3D with parallel shedding; the model is strictly 2D.
"""
import json
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/exploratory")

A, B, C = -3.3265, 0.1816, 1.600e-4
U_REF = 0.06   # percent
FLOOR = 2.0    # percent
KEY = "St_zero_crossing"

names = {
    "medium": "medium_dt0.0025",
    "fine": "fine_dt0.0025",
    "dt_half": "medium_dt0.00125",
    "y30": "medium_dt0.0025_dom-y30",
    "xin30": "medium_dt0.0025_dom-xin30",
    "xout60": "medium_dt0.0025_dom-xout60",
}


def st_ref(re):
    return A / re + B + C * re


def rel(big, small):
    return 100.0 * abs(big - small) / abs(big)


def load(re):
    paths = {k: folder / f"Re{re}_{n}_w120-180.json" for k, n in names.items()}
    missing = [p.name for p in paths.values() if not p.is_file()]
    if missing:
        sys.exit("missing result files: " + ", ".join(missing))
    return {k: json.load(open(p)) for k, p in paths.items()}


print("Reference: Williamson 1989, Eq. (6); U_ref = 0.06 % (stated fit error); floor 2 %; compared value: baseline")
print(f"{'Re':>4s} {'St_ref':>9s} {'St_cfd':>9s} {'diff %':>8s} | {'mesh':>6s} {'dt':>6s} {'domain':>7s} {'U_num':>6s} {'U_ref':>6s} {'band %':>7s} | {'|diff|/band':>11s}  verdict")
for re in (100, 150):
    d = load(re)
    m = d["medium"][KEY]
    mesh = rel(d["fine"][KEY], m)
    dt = rel(d["dt_half"][KEY], m)
    dom = sum(rel(d[c][KEY], m) for c in ("y30", "xin30", "xout60"))
    unum = mesh + dt + dom
    ref = st_ref(re)
    diff = 100.0 * (m - ref) / ref
    band = max(FLOOR, unum + U_REF)
    verdict = "PASS" if abs(diff) <= band else "FAIL"
    print(f"{re:4d} {ref:9.5f} {m:9.5f} {diff:+8.3f} | {mesh:6.3f} {dt:6.3f} {dom:7.3f} {unum:6.3f} {U_REF:6.2f} {band:7.3f} | {abs(diff) / band:11.2f}  {verdict}")
    fft = d["medium"]["St_fft"]
    print(f"      (FFT St of the baseline: {fft:.5f}, differs from zero-crossing by {100.0 * (fft - m) / m:+.3f} %)")
print("Caveats: experimental data are 3D with parallel shedding, the model is 2D; Re 100 and 150 lie inside the")
print("stated range of the fit (49-178); U_ref is the fit error, not the full measurement uncertainty.")
