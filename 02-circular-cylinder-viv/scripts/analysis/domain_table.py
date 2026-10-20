#!/usr/bin/env python3
"""Domain-size comparison, fixed cylinder, Re = 100, medium mesh, dt = 0.0025.

Reads the window results (t = 120-180) written by force_signal.py and prints

  Table A: the D7b table. Per quantity, the absolute change of each
           single-boundary run (y30, xin30, xout60) relative to the enlarged-
           domain value, their sum (the domain-size term of the validation
           rule), and the replicate scatter (regenerated baseline mesh).
           A change smaller than the scatter is flagged "not resolved"
           (it is still counted at its measured value).

  Table B: upstream convergence (decision D7c). Signed change of the 15 -> 30
           step (baseline -> xin30) and of the 30 -> 60 step (xin30 -> xin60),
           each relative to the larger-domain value. Rule fixed before the
           xin60 run: converging if |30 -> 60| < 0.5 * |15 -> 30|.
           The baseline -> xin60 total is printed next to the xin30 term used
           in Table A, to show how much of the upstream effect the D7b term
           does not contain.

Usage: domain_table.py [exploratory_dir]
"""
import json
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/exploratory")

files = {
    "base":   "Re100_medium_dt0.0025_w120-180.json",
    "y30":    "Re100_medium_dt0.0025_dom-y30_w120-180.json",
    "xin30":  "Re100_medium_dt0.0025_dom-xin30_w120-180.json",
    "xout60": "Re100_medium_dt0.0025_dom-xout60_w120-180.json",
    "regen":  "Re100_medium_dt0.0025_dom-regen_w120-180.json",
    "xin60":  "Re100_medium_dt0.0025_dom-xin60_w120-180.json",
}
quantities = [
    ("St_zero_crossing", "St"),
    ("Cd_mean", "Cd_mean"),
    ("Cl_rms", "Cl_rms"),
    ("Cl_amplitude", "Cl_amp"),
]

missing = [f for f in files.values() if not (folder / f).is_file()]
if missing:
    print("missing result files in", folder)
    for m in missing:
        print("  ", m)
    print("files present:")
    for p in sorted(folder.glob("Re100_*_w120-180.json")):
        print("  ", p.name)
    sys.exit(1)

data = {k: json.load(open(folder / v)) for k, v in files.items()}


def val(case, key):
    return data[case][key]


def rel_abs(big, small):
    """Absolute change in percent, relative to the enlarged-domain value."""
    return 100.0 * abs(big - small) / abs(big)


def rel_signed(big, small):
    """Signed change (enlarged minus smaller) in percent, relative to the larger-domain value."""
    return 100.0 * (small - big) / abs(big)


print("Windows (t_start..t_end, periods):")
for k in files:
    d = data[k]
    print(f"  {k:7s} {d['t_start']:8.3f} .. {d['t_end']:8.3f}  {d['n_periods']} periods")

print("\nTable A - D7b: domain-size term (% of enlarged-domain value)")
print(f"{'quantity':10s} {'base':>10s} {'y30':>10s} {'xin30':>10s} {'xout60':>10s} {'regen':>10s} |"
      f" {'dy30%':>7s} {'dxin%':>7s} {'dxout%':>7s} {'sum%':>7s} {'repl%':>7s}  not-resolved")
for key, label in quantities:
    b = val("base", key)
    big = {c: val(c, key) for c in ("y30", "xin30", "xout60")}
    d = {c: rel_abs(big[c], b) for c in big}
    s = sum(d.values())
    repl = rel_abs(val("regen", key), b)
    nr = [c for c in d if d[c] < repl]
    print(f"{label:10s} {b:10.5f} {big['y30']:10.5f} {big['xin30']:10.5f} {big['xout60']:10.5f}"
          f" {val('regen', key):10.5f} | {d['y30']:7.3f} {d['xin30']:7.3f} {d['xout60']:7.3f}"
          f" {s:7.3f} {repl:7.3f}  {','.join(nr) if nr else '-'}")

print("\nTable B - upstream convergence (D7c): signed change, % of larger-domain value")
print(f"{'quantity':10s} {'base':>10s} {'xin30':>10s} {'xin60':>10s} |"
      f" {'15->30':>8s} {'30->60':>8s} {'ratio':>6s}  rule  | {'15->60':>8s} {'D7b xin30 term':>15s}")
for key, label in quantities:
    b, x30, x60 = val("base", key), val("xin30", key), val("xin60", key)
    s1 = rel_signed(x30, b)
    s2 = rel_signed(x60, x30)
    s3 = rel_signed(x60, b)
    ratio = abs(s2) / abs(s1) if s1 != 0 else float("nan")
    verdict = "converging" if abs(s2) < 0.5 * abs(s1) else "NOT converging"
    print(f"{label:10s} {b:10.5f} {x30:10.5f} {x60:10.5f} | {s1:8.3f} {s2:8.3f} {ratio:6.2f}  {verdict:14s}"
          f"| {s3:8.3f} {abs(s1):15.3f}")
print("\nSign convention in Table B: (smaller-domain value - larger-domain value) / |larger-domain value|.")
