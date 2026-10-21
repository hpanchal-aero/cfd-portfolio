#!/usr/bin/env python3
"""Verification summary for the fixed cylinder (baseline: medium mesh, dt = 0.0025, baseline domain).

Usage: verification_table.py <Re> [exploratory_dir]        (Re = 100 or 150)

Terms, per quantity, all in percent of the finer / larger-domain value:
  mesh     : medium -> fine mesh, dt = 0.0025
  dt       : dt = 0.0025 -> 0.00125, medium mesh (the last time-step halving)
  domain   : sum of the single-boundary changes (y = +/-30, x_in = 30, x_out = 60), decision D7b
  U_num    : mesh + dt + domain
  headroom : floor - U_num. The agreement band is max(floor, U_num + U_ref), so the floor decides
             unless the reference uncertainty U_ref is larger than this headroom.
Floors (fixed before any reference value was read): St 2 %, mean Cd 3 %, Cl rms 10 %.
Cl amplitude has no floor and gets no verdict.
If a replicate (regenerated baseline mesh) exists for this Re, its scatter is printed as the
resolution limit of these terms.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("usage: verification_table.py <Re> [exploratory_dir]")
Re = sys.argv[1]
folder = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results/exploratory")

names = {
    "medium": "medium_dt0.0025",
    "fine": "fine_dt0.0025",
    "dt_half": "medium_dt0.00125",
    "y30": "medium_dt0.0025_dom-y30",
    "xin30": "medium_dt0.0025_dom-xin30",
    "xout60": "medium_dt0.0025_dom-xout60",
}
regen_name = "medium_dt0.0025_dom-regen"


def path(n):
    return folder / f"Re{Re}_{n}_w120-180.json"


missing = [path(n).name for n in names.values() if not path(n).is_file()]
if missing:
    print("missing result files in", folder)
    for m in missing:
        print("  ", m)
    print("files present for this Re:")
    for p in sorted(folder.glob(f"Re{Re}_*_w120-180.json")):
        print("  ", p.name)
    sys.exit(1)

data = {k: json.load(open(path(n))) for k, n in names.items()}
regen = json.load(open(path(regen_name))) if path(regen_name).is_file() else None

quantities = [
    ("St_zero_crossing", "St", 2.0),
    ("Cd_mean", "Cd_mean", 3.0),
    ("Cl_rms", "Cl_rms", 10.0),
    ("Cl_amplitude", "Cl_amp", None),
]


def rel(big, small):
    """Absolute change in percent, relative to the finer / larger-domain value."""
    return 100.0 * abs(big - small) / abs(big)


print(f"Re = {Re}: verification terms (% of the finer / larger-domain value), window t = 120-180")
print(f"{'quantity':9s} {'medium':>9s} | {'mesh':>6s} {'dt':>6s} | {'y30':>6s} {'xin30':>6s} {'xout60':>6s} {'domain':>7s} |"
      f" {'U_num':>6s} {'floor':>6s} {'headroom':>8s}  dominant")
for key, label, floor in quantities:
    m = data["medium"][key]
    mesh = rel(data["fine"][key], m)
    dt = rel(data["dt_half"][key], m)
    dom = {c: rel(data[c][key], m) for c in ("y30", "xin30", "xout60")}
    dsum = sum(dom.values())
    u = mesh + dt + dsum
    terms = {"mesh": mesh, "dt": dt, "domain": dsum}
    dominant = max(terms, key=terms.get)
    fl = "-" if floor is None else f"{floor:.1f}"
    hd = "-" if floor is None else f"{floor - u:.2f}"
    print(f"{label:9s} {m:9.5f} | {mesh:6.3f} {dt:6.3f} | {dom['y30']:6.3f} {dom['xin30']:6.3f} {dom['xout60']:6.3f} {dsum:7.3f} |"
          f" {u:6.3f} {fl:>6s} {hd:>8s}  {dominant}")

if regen is not None:
    print("replicate scatter (% of the replicate value): " +
          "  ".join(f"{label} {rel(regen[key], data['medium'][key]):.3f}" for key, label, _ in quantities))
else:
    print(f"no replicate was run at Re = {Re}: the resolution limit of the terms is not measured here")
print("Windows used (t_start .. t_end, whole periods):")
for k in names:
    d = data[k]
    print(f"  {k:7s} {d['t_start']:8.3f} .. {d['t_end']:8.3f}  {d['n_periods']} periods")
