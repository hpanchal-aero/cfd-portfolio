#!/usr/bin/env python3
"""Code-to-code comparison of the fixed cylinder at Re = 150 with 2D numerical references.

Usage: validation_henderson.py [exploratory_dir]

Mean Cd (verdict, rule of notes/02-validation-criteria.md: "should pass", floor 3 %):
  R. D. Henderson, Phys. Fluids 7, 2102 (1995), Table I, fits to his 2D spectral-element simulations of
  the vortex-shedding regime (mean over the shedding cycle, C_D = 2 F / (rho U^2 d l)):
      C_Df = a0 / Re^a1                      a0 = 2.5818, a1 = 0.4369
      C_Dp = a0 - a1 * Re^a2 * exp(a3 * Re)  a0 = 1.4114, a1 = 0.2668, a2 = 0.1648, a3 = -3.375e-3
  The coefficients were read from the page image of the PDF. The paper calls them "simple fits to the measured
  data"; it states no uncertainty, so U_ref = 0 and the floor decides (rule of note 02).
St (no verdict; the verdict against Williamson (1989) is in validation_st.py): fits of
  C. H. K. Williamson and G. L. Brown, J. Fluids Struct. 12, 1073-1085 (1998) to Henderson's 2D numerical data:
      Eq. (17): S = 0.2731 - 1.1129/sqrt(Re) + 0.4821/Re   (average error-of-fit 0.0004)
      abstract: S = 0.2698 - 1.0271/sqrt(Re)               (two-term fit)
band = max(floor, U_num + U_ref), U_num = mesh + time-step + domain term, as in validation_st.py. The domain term
is the change from the baseline to dom-big2. Rows: baseline (verdict), big = production domain dom-big (mesh and
dt terms of the baseline, domain term = step to dom-big2; verdict), big2 (no verdict).
This is code-to-code consistency with 2D simulations, not validation against experiment.
"""
import json
import math
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/exploratory")
RE = 150
FLOOR_CD = 3.0   # percent
U_REF_CD = 0.0   # percent: the source states no uncertainty


def cd_henderson(re):
    cdf = 2.5818 / re ** 0.4369
    cdp = 1.4114 - 0.2668 * re ** 0.1648 * math.exp(-3.375e-3 * re)
    return cdf, cdp, cdf + cdp


def st_wb17(re):
    return 0.2731 - 1.1129 / math.sqrt(re) + 0.4821 / re


def st_abstract(re):
    return 0.2698 - 1.0271 / math.sqrt(re)


def rel(big, small):
    return 100.0 * abs(big - small) / abs(big)


def load(tag):
    p = folder / ("Re%d_%s_w120-180.json" % (RE, tag))
    if not p.is_file():
        sys.exit("missing result file: " + p.name)
    return json.load(open(p))


med = load("medium_dt0.0025")
fine = load("fine_dt0.0025")
dth = load("medium_dt0.00125")
big = load("medium_dt0.0025_dom-big")
big2 = load("medium_dt0.0025_dom-big2")

cdf, cdp, cd_ref = cd_henderson(RE)
print("Henderson (1995) fit at Re = %d: C_Df = %.5f, C_Dp = %.5f, C_D = %.5f" % (RE, cdf, cdp, cd_ref))

m = med["Cd_mean"]
mesh = rel(fine["Cd_mean"], m)
dt = rel(dth["Cd_mean"], m)
print("\nMean Cd against Henderson (floor %.1f %%, U_ref = %.1f %%)" % (FLOOR_CD, U_REF_CD))
print("%-9s %9s %9s | %6s %6s %7s %6s %7s | %11s  %s" % (
    "row", "Cd_ref", "Cd_cfd", "mesh", "dt", "domain", "U_num", "band %", "diff %", "verdict"))
rows = (("baseline", m, rel(big2["Cd_mean"], m), True),
        ("big", big["Cd_mean"], rel(big2["Cd_mean"], big["Cd_mean"]), True),
        ("big2", big2["Cd_mean"], None, False))
for name, v, dom, with_verdict in rows:
    diff = 100.0 * (v - cd_ref) / cd_ref
    if with_verdict:
        unum = mesh + dt + dom
        band = max(FLOOR_CD, unum + U_REF_CD)
        verdict = "PASS" if abs(diff) <= band else "FAIL"
        print("%-9s %9.5f %9.5f | %6.3f %6.3f %7.3f %6.3f %7.3f | %+11.3f  %s (%.2f of band)" % (
            name, cd_ref, v, mesh, dt, dom, unum, band, diff, verdict, abs(diff) / band))
    else:
        print("%-9s %9.5f %9.5f | %6s %6s %7s %6s %7s | %+11.3f  no verdict (its own domain term is not measured)" % (
            name, cd_ref, v, "-", "-", "-", "-", "-", diff))

print("\nSt against 2D numerical fits (code-to-code, no verdict)")
print("%-9s %9s | %9s %9s" % ("row", "St_cfd", "vs Eq.17", "vs abstr."))
r17, rab = st_wb17(RE), st_abstract(RE)
print("%-9s %9s | %9.5f %9.5f   (reference values)" % ("", "", r17, rab))
for name, d in (("baseline", med), ("big", big), ("big2", big2)):
    s = d["St_zero_crossing"]
    print("%-9s %9.5f | %+8.3f%% %+8.3f%%" % (name, s, 100.0 * (s - r17) / r17, 100.0 * (s - rab) / rab))

print("\nCaveats: Henderson's domain is not stated in the pages that were read; the domain series of our own runs")
print("had not converged (step big -> big2: St %.3f %%, Cd %.3f %%); the sign of the domain effect on Cd is away"
      % (rel(big2["St_zero_crossing"], big["St_zero_crossing"]), rel(big2["Cd_mean"], big["Cd_mean"])))
print("from Henderson's value. The Henderson coefficients were read from a page image of the PDF.")
