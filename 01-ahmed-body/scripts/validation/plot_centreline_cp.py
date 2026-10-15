"""Surface Cp near the symmetry plane and a regional pressure-drag decomposition.

NORMAL CONVENTION: OpenFOAM patch normals point OUT OF THE FLUID, i.e. INTO the body.
Roof/slant faces (fluid above) therefore have n_z < 0; underside faces have n_z > 0;
nose faces have n_x > 0; the rear face has n_x < 0. The pressure force on the body
is F = sum(p * n_patch * A).

Cp = 2*(pMean - p_ref)/U_inf^2, p_ref = pMean at an upstream free-stream point
(x = -1.2 m, y = 0.05, z = 0.70). p is kinematic (rho = 1 convention).
Cd contribution of a region = 2*sum((p - p_ref) * n_x * A) / (U^2 * Aref), Aref = half-body area.
--case label,U,volume_vtk,patch_vtk,Cd_total[,slant_angle_deg]
The slant angle (default 25) sets where the slant region starts, x = 1.044 - 0.222*cos(angle).
The slant region is selected by its normal (-0.95 < n_z < -0.5), which suits angles of
about 20 deg and above (a 10 deg slant has n_z = -0.985 and would not be selected)."""
import argparse
import numpy as np
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AREF = 0.056016
Y_BAND = 0.02
REF_PTS = [(-2.0, 0.05, 0.70), (-1.2, 0.05, 0.70), (-0.4, 0.05, 0.70)]
REF_IDX = 1
X_REAR = 1.044
SLANT_LEN = 0.222
X_FRONT = 0.10

ap = argparse.ArgumentParser()
ap.add_argument("--case", action="append", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

fig, ax = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
slant_marks = []   # (x_slant_start, colour, angle)
for spec, col in zip(a.case, ("tab:blue", "tab:red", "tab:green")):
    parts = spec.split(",")
    label, U, vol, patch, cd_tot = parts[:5]
    angle = float(parts[5]) if len(parts) > 5 else 25.0
    U, cd_tot = float(U), float(cd_tot)
    x_slant = X_REAR - SLANT_LEN * np.cos(np.radians(angle))
    slant_marks.append((x_slant, col, angle))
    v = pv.read(vol)
    pm = np.asarray(pv.PolyData(np.array(REF_PTS)).sample(v)["pMean"])
    pref = pm[REF_IDX]
    print("\n%s: Cp (outlet-ref) at x=-2.0,-1.2,-0.4: %s ; p_ref = %.4f (x=-1.2)" % (label, np.round(2 * pm / U ** 2, 4), pref))
    p = pv.read(patch).compute_cell_sizes(length=False, area=True, volume=False)
    p = p.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False)
    c = p.cell_centers().points
    n = np.asarray(p.cell_data["Normals"])
    A = np.asarray(p.cell_data["Area"])
    dp = np.asarray(p.cell_data["pMean"]) - pref
    cp = 2.0 * dp / U ** 2
    band = c[:, 1] < Y_BAND
    panels = (("underside (n_z>0.5)", band & (n[:, 2] > 0.5)),
              ("roof + slant (n_z<-0.5)", band & (n[:, 2] < -0.5)))
    for k, (name, m) in enumerate(panels):
        o = np.argsort(c[m, 0])
        ax[k].plot(c[m, 0][o], cp[m][o], ".", ms=2, color=col, label="%s (U=%g)" % (label, U))
        ax[k].set_title("Cp, %s, y<%.0f mm" % (name, 1000 * Y_BAND))
        i = np.argmin(cp[m])
        print("  %-24s faces %5d  min Cp %.3f at x=%.3f" % (name, m.sum(), cp[m][i], c[m, 0][i]))
    # --- regional pressure drag (all faces of the half-body patch, partition by x / normal)
    base = (c[:, 0] >= X_REAR - 1e-3) & (n[:, 0] < -0.9)
    slant = (c[:, 0] >= x_slant) & (c[:, 0] < X_REAR - 1e-3) & (n[:, 2] < -0.5) & (n[:, 2] > -0.95)
    front = c[:, 0] < X_FRONT
    mid = (c[:, 0] >= X_FRONT) & (c[:, 0] < x_slant)
    other = ~(base | slant | front | mid)
    assert not np.any(base & slant) and not np.any(base & front)
    print("  region           faces      area     Cd_pressure   share_of_total")
    tot = 0.0
    for name, m in (("front  x<0.10", front), ("mid 0.10..slant", mid), ("slant", slant), ("base (rear face)", base), ("other (x>slant)", other)):
        cdr = 2.0 * np.sum(dp[m] * n[m, 0] * A[m]) / (U ** 2 * AREF)
        tot += cdr
        print("  %-17s %6d %9.5f %12.5f %12.1f %%" % (name, m.sum(), A[m].sum(), cdr, 100 * cdr / cd_tot))
    print("  TOTAL pressure Cd %.5f ; total Cd from forceCoeffs %.5f ; friction by difference %.5f (%.1f %%)"
          % (tot, cd_tot, cd_tot - tot, 100 * (cd_tot - tot) / cd_tot))
    print("  face-count check: %d of %d faces assigned" % (int((front | mid | slant | base | other).sum()), len(A)))
same_angle = len({round(s[2], 6) for s in slant_marks}) == 1
for k in (0, 1):
    if same_angle:
        ax[k].axvline(slant_marks[0][0], color="0.6", lw=0.8)
    else:
        for xs, col, ang in slant_marks:
            ax[k].axvline(xs, color=col, lw=0.8, ls=":")
    ax[k].axvline(X_REAR, color="0.6", lw=0.8)
    ax[k].set_xlabel("x [m]")
    ax[k].grid(alpha=0.3)
ax[0].set_ylabel("Cp (ref: upstream free stream)")
ax[0].invert_yaxis()
ax[0].legend(fontsize=8)
fig.tight_layout()
fig.savefig(a.out, dpi=150)
print("\nwrote", a.out)
