#!/usr/bin/python3
"""Compare sampled free-stream k, omega, nut/nu upstream of the nose with the
SST free-stream decay model that fixed the inlet values.
Usage: check_nose_turbulence.py --vtk F --U 60 --k0 0.1051 --omega0 639.8"""
import argparse
import numpy as np
import pyvista as pv

ap = argparse.ArgumentParser()
ap.add_argument("--vtk", required=True)
ap.add_argument("--U", type=float, required=True)
ap.add_argument("--k0", type=float, required=True)
ap.add_argument("--omega0", type=float, required=True)
ap.add_argument("--nu", type=float, default=1.5e-5)
ap.add_argument("--inlet-length", type=float, default=2.088)
a = ap.parse_args()
b, bs = 0.0828, 0.09
m = pv.read(a.vtk)
y, z = 0.05, 0.70
xs = np.array([-2.0, -1.6, -1.2, -0.8, -0.4, -0.2, -0.05])
s = pv.PolyData(np.column_stack([xs, np.full_like(xs, y), np.full_like(xs, z)])).sample(m)
print("valid probe points:", int(np.asarray(s["vtkValidPointMask"]).astype(bool).sum()), "of", len(xs))
cd = s.point_data
print("   x     U_x    k(Mean)   omega   nut/nu   Tu%   | model: k       omega   nut/nu   Tu%")
for i, x in enumerate(xs):
    t = (x + a.inlet_length) / a.U
    km = a.k0 * (1 + b * a.omega0 * t) ** (-bs / b)
    wm = a.omega0 / (1 + b * a.omega0 * t)
    k, w, nut = cd["kMean"][i], cd["omega"][i], cd["nut"][i]
    print("%6.2f %6.2f  %.6f %7.2f %7.2f  %.3f  | %.6f %7.2f %7.2f  %.3f" %
          (x, cd["UMean"][i][0], k, w, nut / a.nu, 100 * np.sqrt(2 * k / 3) / a.U,
           km, wm, km / wm / a.nu, 100 * np.sqrt(2 * km / 3) / a.U))
