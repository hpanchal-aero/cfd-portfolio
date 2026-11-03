"""sweep_summary.py -- response of the cylinder against the reduced velocity U_r (Re 150, 2-DOF).

Usage (user packages are needed for matplotlib, so no -I here):
    /usr/bin/python3 -E -P scripts/analysis/sweep_summary.py [<out_dir>]

Runs scripts/analysis/body_motion.py for the final window of every case and parses its text output.
  settled cases    : A_y* = (max - min)/2 over whole periods of that window (D19 passed).
  modulated cases  : U_r 3.5 and U_r 4 (D22): bar from the lowest to the highest peak of y, marker at the
                     mean of the peaks over whole modulation cycles; the frequency is the mean frequency of
                     the upward y crossings (two frequencies are present in these records).
  m* = 2 (U_r 6)   : separate marker, with the Verma & De Table I value 0.536 (3D grids) for comparison.
  mesh check       : U_r 6 on the fine mesh (D26), drawn as a ring around the medium-mesh point.
Lines are broken at the modulated cases (they join different states). In the plot the m* = 2 square and the
Table I triangle are offset by -/+ X_OFF in U_r for visibility only.
Writes <out_dir>/sweep_summary.csv and <out_dir>/sweep_response.png (default results/sweep).
"""
import csv
import os
import re
import subprocess
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BODY = "scripts/analysis/body_motion.py"
PRE = "cases/moving_Re150_Ur%s_dom-big_medium_dt0.0025_pre"
MS = 2.546
X_OFF = 0.12

# label, U_r, m*, case dir, t0, t1
SETTLED = [
    ("Ur3", 3.0, MS, PRE % "3", 442, 500),
    ("Ur4.5", 4.5, MS, PRE % "4.5", 342, 400),
    ("Ur5", 5.0, MS, "cases/moving_Re150_Ur5_dom-big_medium_dt0.0025", 342, 400),
    ("Ur6", 6.0, MS, PRE % "6", 342, 400),
    ("Ur7", 7.0, MS, PRE % "7", 342, 398),
    ("Ur7.5", 7.5, MS, PRE % "7.5", 342, 400),
    ("Ur7.75", 7.75, MS, PRE % "7.75", 442, 500),
    ("Ur8", 8.0, MS, PRE % "8", 645, 697),
    ("Ur11", 11.0, MS, PRE % "11", 442, 500),
    ("Ur17", 17.0, MS, PRE % "17", 342, 400),
]
MODULATED = [
    ("Ur3.5", 3.5, MS, PRE % "3.5", 284, 476),
    ("Ur4", 4.0, MS, PRE % "4", 250, 552),
]
MSTAR2 = ("Ur6_ms2", 6.0, 2.0, "cases/moving_Re150_Ur6_dom-big_medium_dt0.0025_pre_ms2", 442, 500)
FINE = ("Ur6_fine", 6.0, MS, "cases/moving_Re150_Ur6_dom-big_fine_dt0.0025_pre", 342, 400)
TABLE_I_AY = 0.536   # Verma & De Table I, Re 150, m* 2, U_r 6, 3D grids (as reported by the earlier paper summary)

RX_AMP = re.compile(r"y amplitude \(max-min\)/2 = ([0-9.]+), mean y = ([-+0-9.]+), mean x = ([-+0-9.]+)")
RX_FRQ = re.compile(r"body period ([0-9.]+), frequency ([0-9.]+)")
RX_CD = re.compile(r"mean Cd = ([-+0-9.]+), mean Cl = ([-+0-9.]+), Cl rms about mean = ([0-9.]+)")
RX_PK = re.compile(r"^\s+(\d+\.\d+)\s+([+-]\d\.\d+)\s*$", re.M)


def run_body(case, t0, t1):
    out = subprocess.run(["/usr/bin/python3", "-I", BODY, case, str(t0), str(t1)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("body_motion.py failed for %s [%s,%s]:\n%s" % (case, t0, t1, out.stderr[-500:]))
    s = out.stdout
    ma, mf, mc = RX_AMP.search(s), RX_FRQ.search(s), RX_CD.search(s)
    if not (ma and mf and mc):
        sys.exit("could not parse body_motion.py output for %s [%s,%s]" % (case, t0, t1))
    pk = np.array([(float(a), float(b)) for a, b in RX_PK.findall(s)])
    return dict(A=float(ma.group(1)), mean_x=float(ma.group(3)), f=float(mf.group(2)),
                Cd=float(mc.group(1)), Cl_rms=float(mc.group(3))), pk


def segments(settled, modulated):
    """Split the settled rows (sorted by U_r) wherever a modulated U_r lies between two neighbours."""
    mod_ur = [r["U_r"] for r in modulated]
    segs, cur = [], []
    for r in settled:
        if cur and any(cur[-1]["U_r"] < u < r["U_r"] for u in mod_ur):
            segs.append(cur)
            cur = []
        cur.append(r)
    if cur:
        segs.append(cur)
    return segs


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "results/sweep"
    os.makedirs(out_dir, exist_ok=True)
    rows = []

    def add(lab, ur, ms, case, t0, t1, kind):
        r, pk = run_body(case, t0, t1)
        row = dict(label=lab, U_r=ur, m_star=ms, window="%g-%g" % (t0, t1), kind=kind,
                   A_high=r["A"], A_low="", A_cycle_mean="", f=r["f"], f_over_fn=r["f"] * ur,
                   mean_Cd=r["Cd"], Cl_rms=r["Cl_rms"], mean_x=r["mean_x"])
        if kind == "modulated":
            v = pk[(pk[:, 0] >= t0) & (pk[:, 0] < t1), 1]
            row["A_high"], row["A_low"], row["A_cycle_mean"] = v.max(), v.min(), v.mean()
        rows.append(row)

    for c in SETTLED:
        add(*c, "settled")
    for c in MODULATED:
        add(*c, "modulated")
    add(*MSTAR2, "settled_ms2")
    add(*FINE, "mesh_check")
    rows.sort(key=lambda r: (r["U_r"], r["kind"]))

    cols = ["label", "U_r", "m_star", "window", "kind", "A_high", "A_low", "A_cycle_mean",
            "f", "f_over_fn", "mean_Cd", "Cl_rms", "mean_x"]
    with open(os.path.join(out_dir, "sweep_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (("%.5g" % v) if isinstance(v, float) else v) for k, v in r.items() if k in cols})

    print("%-8s %6s %5s %-9s %-12s %8s %8s %8s %8s %8s %8s" % (
        "label", "U_r", "m*", "window", "kind", "A_high", "A_low", "A_mean", "f", "f/f_n", "Cd"))
    for r in rows:
        fmt = lambda x: ("%8.4f" % x) if x != "" else "%8s" % "-"
        print("%-8s %6g %5g %-9s %-12s %s %s %s %s %s %s" % (
            r["label"], r["U_r"], r["m_star"], r["window"], r["kind"], fmt(r["A_high"]), fmt(r["A_low"]),
            fmt(r["A_cycle_mean"]), fmt(r["f"]), fmt(r["f_over_fn"]), fmt(r["mean_Cd"])))

    st = [r for r in rows if r["kind"] == "settled"]
    md = [r for r in rows if r["kind"] == "modulated"]
    m2 = [r for r in rows if r["kind"] == "settled_ms2"][0]
    fine = [r for r in rows if r["kind"] == "mesh_check"][0]
    segs = segments(st, md)

    fig, ax = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    for key, a in (("A_high", ax[0]), ("f_over_fn", ax[1]), ("mean_Cd", ax[2])):
        for i, seg in enumerate(segs):
            a.plot([r["U_r"] for r in seg], [r[key] for r in seg], "o-", color="C0",
                   label="settled (D19)" if (i == 0 and key == "A_high") else None)

    for r in md:
        ax[0].plot([r["U_r"]] * 2, [r["A_low"], r["A_high"]], "-", color="C1", lw=3)
        ax[0].plot(r["U_r"], r["A_cycle_mean"], "D", color="C1")
        ax[1].plot(r["U_r"], r["f_over_fn"], "o", mfc="none", color="C1")
        ax[2].plot(r["U_r"], r["mean_Cd"], "o", mfc="none", color="C1")
    ax[0].plot([], [], "-", color="C1", lw=3, label="modulated: lowest to highest peak")
    ax[0].plot([], [], "D", color="C1", label="modulated: mean of peaks over whole cycles")
    ax[1].plot([], [], "o", mfc="none", color="C1", label="modulated (D22): less certain")
    ax[2].plot([], [], "o", mfc="none", color="C1", label="modulated (D22): Cd uncertain by 1-2 %")

    ax[0].plot(fine["U_r"], fine["A_high"], "o", mfc="none", mec="C2", ms=12, mew=2,
               label="fine mesh, U_r 6 (D26)")
    ax[0].plot(m2["U_r"] + X_OFF, m2["A_high"], "s", color="C3", ms=8,
               label="m* = 2 (this work), offset +%.2f in U_r" % X_OFF)
    ax[0].plot(6.0 - X_OFF, TABLE_I_AY, "^", mfc="none", mec="k", ms=10, mew=1.5,
               label="Verma & De Table I, m* = 2 (3D grids), offset -%.2f" % X_OFF)

    ax[1].axhline(1.0, color="k", lw=0.8, ls="--")
    ax[0].set_ylabel("A_y* = transverse amplitude / D")
    ax[1].set_ylabel("response frequency / f_n")
    ax[2].set_ylabel("mean Cd")
    ax[2].set_xlabel("reduced velocity U_r = U / (f_n D)")
    ax[0].legend(fontsize=7, loc="upper right")
    ax[1].legend(fontsize=7, loc="lower right")
    ax[2].legend(fontsize=7, loc="upper right")
    for a in ax:
        a.grid(alpha=0.3)
    ax[0].set_title("Re 150, 2-DOF, m* = 2.546, zeta = 0\n(domain 30/30/60 D, medium mesh except the fine-mesh marker)")
    fig.tight_layout()
    path = os.path.join(out_dir, "sweep_response.png")
    fig.savefig(path, dpi=150)
    print("saved", path, "and", os.path.join(out_dir, "sweep_summary.csv"))


if __name__ == "__main__":
    main()
