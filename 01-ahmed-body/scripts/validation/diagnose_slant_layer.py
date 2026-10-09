#!/usr/bin/python3
"""Slant-layer diagnostics: (1) vertical sampling lines above the slant at 1 mm
spacing -> mean U and number of distinct cells crossed in the first 30 mm;
(2) yPlus statistics on slant faces of the ahmedBody patch.
Geometry (our frame, mm): slant from (x=842.6, z=338) to (1044, 243.2+...) computed
from SLANT_LEN and angle; ERCOFTAC x_data = x_ours - 1044."""
import argparse
import numpy as np
import pyvista as pv

X_REAR_MM, ROOF_Z_MM, SLANT_DEG, SLANT_LEN_MM = 1044.0, 338.0, 25.0, 222.0
T = np.tan(np.radians(SLANT_DEG))
X0 = -SLANT_LEN_MM * np.cos(np.radians(SLANT_DEG))     # x_data of slant start


def zsurf(xd):
    return ROOF_Z_MM - (xd - X0) * T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vtk", required=True)
    ap.add_argument("--patch", required=True)
    a = ap.parse_args()
    m = pv.read(a.vtk)
    print("station  zsurf  | cells crossed in 0-30 mm | U(mean) at +1,+5,+10,+15,+20,+30 mm above surface")
    for xd in (-143.0, -103.0, -63.0, -23.0, -3.0):
        h = np.arange(0.5, 30.01, 1.0)                 # vertical offsets above surface [mm]
        z = (zsurf(xd) + h) / 1000.0
        x = np.full_like(z, (xd + X_REAR_MM) / 1000.0)
        s = pv.PolyData(np.column_stack([x, np.full_like(z, 1e-4), z])).sample(m)
        ok = np.asarray(s["vtkValidPointMask"]).astype(bool)
        cid = np.asarray(s["cellID"])[ok]
        U = np.asarray(s["UMean"])[:, 0]
        pick = [np.argmin(abs(h - v)) for v in (1, 5, 10, 15, 20, 30)]
        print("%7.1f %6.1f | %3d distinct (of %d valid) | %s" %
              (xd, zsurf(xd), len(np.unique(cid)), int(ok.sum()),
               " ".join("%5.1f" % U[i] for i in pick)))
    p = pv.read(a.patch)
    p = p.compute_normals(cell_normals=True, point_normals=False, auto_orient_normals=False)
    c = p.cell_centers().points * 1000.0
    n = np.asarray(p.cell_data["Normals"])
    yp = np.asarray(p.cell_data["yPlus"])
    ang = np.degrees(np.arccos(np.clip(np.abs(n[:, 2]), 0, 1)))
    sl = (c[:, 0] >= X_REAR_MM + X0) & (c[:, 0] <= X_REAR_MM) & (abs(ang - SLANT_DEG) < 3.0)
    print("\nslant faces selected: %d of %d patch faces" % (sl.sum(), len(yp)))
    y = yp[sl]
    print("yPlus on slant faces: min %.1f  p10 %.1f  median %.1f  mean %.1f  p90 %.1f  max %.1f"
          % (y.min(), *np.percentile(y, [10, 50]), y.mean(), np.percentile(y, 90), y.max()))
    print("fraction in target band 30-300: %.3f   below 30: %.3f   above 300: %.3f"
          % (np.mean((y >= 30) & (y <= 300)), np.mean(y < 30), np.mean(y > 300)))
    yall = yp[yp > 0]
    print("whole body patch yPlus (>0): min %.1f median %.1f max %.1f" % (yall.min(), np.median(yall), yall.max()))


if __name__ == "__main__":
    main()
