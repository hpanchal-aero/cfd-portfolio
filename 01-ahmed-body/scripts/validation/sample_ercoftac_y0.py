#!/usr/bin/python3
"""Sample the iteration-averaged Ahmed-body solution at the ERCOFTAC AC1-05
(Lienhart et al. 2000, Exp2) y = 0 measurement points and evaluate the pre-stated
criteria (+ C5 report).

--angle 25 (default): criteria C2-C4 as approved 2026-10-04/05 (attached slant flow
measured: C2 = no reversed flow above the slant; C3 window 138-288 mm).
--angle 35: criteria C2'-C4' as approved 2026-10-11 (separated slant flow measured):
  C2'  reversed flow at every measured slant station x = -123..-3 mm and the first
       reversed station in {-163, -143, -123} (measured onset: -143);
  C3a' reversed flow at focus stations 17, 37, 87 and global stations 137, 187, 237, 287;
  C3b' CFD recirculation-end interval inside the window [237, 387] mm
       (measured end interval (287, 337]; +-50 mm, a convention);
  C4'  pooled NRMSE of U and W / Ub with the 25 deg thresholds (<=0.05 good, <=0.10 fair).

Frame: ERCOFTAC x = 0 is the rear base -> x_ours = x_data/1000 + 1.044;
z = 0 is the floor in both frames. Declared units in the .dat files are 'm'
but the values are mm. Probes sit at y = Y_OFF (just off the symmetry plane).
"""
import argparse, os
import numpy as np
import pyvista as pv

X_REAR = 1.044
UB = 40.0
Y_OFF = 1.0e-4
SLANT_LEN_MM = 222.0


def load_dat(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if s and not s.startswith(("#", "%")):
                rows.append([float(v) for v in s.split()])
    return np.array(rows)


def sample_file(mesh, a):
    x = a[:, 0] / 1000.0 + X_REAR
    z = a[:, 2] / 1000.0
    pts = pv.PolyData(np.column_stack([x, np.full_like(x, Y_OFF), z]))
    s = pts.sample(mesh)
    ok = np.asarray(s["vtkValidPointMask"]).astype(bool)
    U = np.asarray(s["UMean"])
    return dict(x=a[:, 0], z=a[:, 2], ok=ok,
                Ue=a[:, 3], We=a[:, 5], Uc=U[:, 0], Wc=U[:, 2],
                ke=0.5 * (a[:, 6] ** 2 + a[:, 7] ** 2 + a[:, 8] ** 2),
                kc=np.asarray(s["kMean"]))


def sel(d, xlo, xhi):
    m = (d["x"] >= xlo) & (d["x"] <= xhi)
    return {k: v[m] for k, v in d.items()}


def nrmse(d):
    ok = d["ok"]
    if ok.sum() == 0:
        return np.nan, np.nan, np.nan
    eu = d["Uc"][ok] - d["Ue"][ok]
    ew = d["Wc"][ok] - d["We"][ok]
    pooled = np.sqrt(np.mean(np.concatenate([eu, ew]) ** 2)) / UB
    return pooled, np.sqrt(np.mean(eu ** 2)) / UB, np.sqrt(np.mean(ew ** 2)) / UB


def station_rows(d):
    out = []
    for x in np.unique(d["x"]):
        s = sel(d, x, x)
        ok = s["ok"]
        out.append((x, len(ok), int(ok.sum()), int(np.sum(s["Ue"] < 0)),
                    int(np.sum(ok & (s["Uc"] < 0))), s["Ue"].min(),
                    np.min(s["Uc"][ok]) if ok.any() else np.nan, nrmse(s)[0]))
    return out


def print_rows(title, rows):
    print("\n" + title)
    print("  x_mm    n valid rev_exp rev_cfd   Umin_exp   Umin_cfd  NRMSE(U,W)/Ub")
    for r in rows:
        print("%7.1f %4d %5d %7d %7d %10.2f %10.2f %12.4f" % r)


def end_interval(rows, col):
    xs = [r[0] for r in rows]
    rev = [r[0] for r in rows if r[col] > 0]
    if not rev:
        return None, xs[0]
    xl = max(rev)
    i = xs.index(xl)
    return xl, (xs[i + 1] if i + 1 < len(xs) else None)


def has_reversed(rows, x):
    """True only if station x exists in rows and the CFD has reversed flow there."""
    for r in rows:
        if abs(r[0] - x) < 1e-6:
            return r[4] > 0
    return False


def grade(v):
    return "good" if v <= 0.05 else ("fair" if v <= 0.10 else "poor")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vtk", required=True)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--angle", type=int, choices=(25, 35), default=25)
    args = ap.parse_args()
    angle = args.angle
    os.makedirs(args.out_dir, exist_ok=True)
    mesh = pv.read(args.vtk)
    G = sample_file(mesh, load_dat(os.path.join(args.data_dir, "Ahmed_%d_y=0_global.dat" % angle)))
    F = sample_file(mesh, load_dat(os.path.join(args.data_dir, "Ahmed_%d_y=0_focus.dat" % angle)))
    for name, d in (("global", G), ("focus", F)):
        print("%s: %d points, %d valid (in fluid mesh), %d invalid"
              % (name, len(d["ok"]), d["ok"].sum(), (~d["ok"]).sum()))
    slant_x0 = -SLANT_LEN_MM * np.cos(np.radians(float(angle)))
    print("slant starts at x_data = %.2f mm" % slant_x0)
    slant = sel(F, slant_x0, 0.0)
    wake = sel(G, 1.0, 1e9)
    upstream = sel(G, -1500.0, -1000.0)

    # ---- C2
    sr = station_rows(slant)
    print_rows("SLANT stations (focus file, x_data in [%.1f, 0])" % slant_x0, sr)
    rc, re_ = sum(r[4] for r in sr), sum(r[3] for r in sr)
    if angle == 25:
        print("C2: reversed-flow points above slant: CFD %d, measured %d -> %s"
              % (rc, re_, "PASS" if rc == 0 else "FAIL"))
    else:
        req = (-123.0, -103.0, -83.0, -63.0, -43.0, -23.0, -3.0)
        c2a = all(has_reversed(sr, x) for x in req)
        first_cfd = min((r[0] for r in sr if r[4] > 0), default=None)
        first_exp = min((r[0] for r in sr if r[3] > 0), default=None)
        c2b = first_cfd in (-163.0, -143.0, -123.0)
        print("C2' reversed-flow points above slant: CFD %d, measured %d (report)" % (rc, re_))
        print("C2'a reversed flow at every slant station -123..-3 mm -> %s"
              % ("PASS" if c2a else "FAIL"))
        print("C2'b first reversed station: CFD %s, measured %s; allowed -163, -143, -123 -> %s"
              % (first_cfd, first_exp, "PASS" if c2b else "FAIL"))

    # ---- C3
    if angle != 25:
        fw = station_rows(sel(F, 1.0, 1e9))
        print_rows("WAKE stations (focus file, x_data > 0)", fw)
    wr = station_rows(wake)
    print_rows("WAKE stations (global file, x_data > 0)", wr)
    by_x = {r[0]: r for r in wr}
    xl, xn = end_interval(wr, 4)
    xle, xne = end_interval(wr, 3)
    if angle == 25:
        c3a = all(by_x[x][4] > 0 for x in (38.0, 88.0, 138.0))
        c3b = (xl is not None and xn is not None and xl >= 138.0 and xn <= 288.0)
        print("C3a: reversed flow at 38, 88, 138 mm -> %s" % ("PASS" if c3a else "FAIL"))
        print("C3b: CFD recirculation end in (%s, %s] mm; window [138, 288] -> %s"
              % (xl, xn, "PASS" if c3b else "FAIL"))
    else:
        c3a = (all(has_reversed(fw, x) for x in (17.0, 37.0, 87.0))
               and all(has_reversed(wr, x) for x in (137.0, 187.0, 237.0, 287.0)))
        c3b = (xl is not None and xn is not None and xl >= 237.0 and xn <= 387.0)
        print("C3'a reversed flow at focus 17, 37, 87 and global 137, 187, 237, 287 mm -> %s"
              % ("PASS" if c3a else "FAIL"))
        print("C3'b CFD recirculation end in (%s, %s] mm; window [237, 387] -> %s"
              % (xl, xn, "PASS" if c3b else "FAIL"))
    print("     measured end interval (report only): (%s, %s] mm" % (xle, xne))

    # ---- C4
    both = {k: np.concatenate([slant[k], wake[k]]) for k in slant}
    for lab, d in (("slant+wake (C4)", both), ("slant only", slant), ("wake only", wake)):
        p, u, w = nrmse(d)
        print("NRMSE/Ub %-16s pooled %.4f (%s)  U %.4f  W %.4f  n_valid %d"
              % (lab, p, grade(p), u, w, int(d["ok"].sum())))

    # ---- C5 (report only)
    print("\nC5 report only: upstream stations (floor boundary layer, modelled k vs measured k)")
    print("  x_mm valid NRMSE(U)/Ub  Ue(28) Uc(28)  ke(28) kc(28)  ke(top) kc(top)")
    for x in np.unique(upstream["x"]):
        s = sel(upstream, x, x)
        ok = s["ok"]
        j0, jt = int(np.argmin(s["z"])), int(np.argmax(s["z"]))
        eu = np.sqrt(np.mean((s["Uc"][ok] - s["Ue"][ok]) ** 2)) / UB if ok.any() else np.nan
        print("%7.1f %5d %11.4f %7.2f %6.2f %7.3f %6.3f %8.3f %7.3f"
              % (x, int(ok.sum()), eu, s["Ue"][j0], s["Uc"][j0], s["ke"][j0],
                 s["kc"][j0], s["ke"][jt], s["kc"][jt]))

    # ---- raw comparison table
    cols = []
    for code, d in ((0, G), (1, F)):
        cols.append(np.column_stack([np.full(len(d["x"]), code), d["x"], d["z"], d["ok"],
                                     d["Ue"], d["Uc"], d["We"], d["Wc"], d["ke"], d["kc"]]))
    out = os.path.join(args.out_dir, "comparison_points.csv")
    np.savetxt(out, np.vstack(cols), delimiter=",", fmt="%.6g",
               header="set(0=global,1=focus),x_mm,z_mm,valid,U_exp,U_cfd,W_exp,W_cfd,k_exp,k_cfd")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
