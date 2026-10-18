# 03 - Fixed cylinder, Re = 100: mesh and time-step verification

Date: 2026-10-18
Status: verification inputs only. No reference value has been read. No
validation verdict is given here.

## Common set-up
- Domain x = -15 .. 30, y = +/-15 (blockage 3.3 %), thickness 0.1,
  D = U = 1, Re = 100 (nu = 0.01), laminar, 2D (one cell layer, empty
  front/back).
- Backward in time; Gauss linear; linearUpwind grad(U) for convection;
  PIMPLE with nOuterCorrectors 1, nCorrectors 2, nNonOrthogonalCorrectors 1.
- Mesh levels coarse / medium / fine = cell size scaled by 1/1.4, 1, 1.4
  (cell counts and quality in note 01; md5 of the mesh used is stored in
  cases/*/mesh.md5 because Gmsh output is not bit-identical between runs).
- Statistics: whole shedding periods inside t = 120 .. 180 (first to last
  Cl up-crossing), 9 periods in every run. Same window and estimator in
  every row below. St from zero crossings (FFT agrees to 4 digits in all
  runs). Cl amplitude = (max - min)/2 over the window.

## Mesh study (dt = 0.0025 on all three)

| mesh   | St      | Cd mean | Cl rms  | Cl amp  | Cl mean  |
|--------|---------|---------|---------|---------|----------|
| coarse | 0.16656 | 1.35610 | 0.22443 | 0.31767 | +0.00251 |
| medium | 0.16717 | 1.35650 | 0.22952 | 0.32478 | -0.00020 |
| fine   | 0.16729 | 1.35774 | 0.23334 | 0.33007 | +0.00101 |

Medium -> fine change as % of the fine value: St 0.070, Cd 0.092,
Cl rms 1.635, Cl amp 1.604.
Ratio of successive changes (c>m)/(m>f): Cd 0.32 (increments grow),
Cl amp 1.34 and Cl rms 1.34 (observed p about 0.9), St 5.2 (not an order).

## Time-step study (medium mesh, same mesh md5 in all three cases)

| dt      | St      | Cd mean | Cl rms  | Cl amp  | period  |
|---------|---------|---------|---------|---------|---------|
| 0.005   | 0.16711 | 1.35798 | 0.23175 | 0.32794 | 5.98407 |
| 0.0025  | 0.16717 | 1.35650 | 0.22952 | 0.32478 | 5.98177 |
| 0.00125 | 0.16721 | 1.35559 | 0.22808 | 0.32290 | 5.98066 |

Last halving as % of the dt = 0.00125 value: Cd 0.066, Cl rms 0.63,
Cl amp 0.58, St 0.018.
The dt = 0.00125 run was restarted at t = 100 from the dt = 0.0025 state;
its per-cycle amplitudes are constant to 4 digits from the first window
cycle, so the restart transient had decayed before t = 120.
Observed order in time from the three levels: Cd 0.72, Cl amp 0.75,
Cl rms 0.62, St/period 1.05.
The pre-run prediction was second order (Cl amp change -0.0008, Cd
-0.0004); observed -0.0019 and -0.0009. Second order is rejected.

## Stability
- dt = 0.005: coarse and medium stable; fine diverged within the first
  steps, and again when restarted from a smooth t = 5 state. dt = 0.0025
  stable on all three meshes. A Courant limit near 0.6 - 0.7 is an
  inference from three runs, not a measurement.
- "Courant Number" lines printed before the first "Time =" line are
  initial-field values and are excluded from in-run maxima.
- Medium, t >= 100: maximum Courant 0.2646 (dt 0.0025) and 0.1323
  (dt 0.00125), ratio 2.000.

## Integrity checks
- Medium dt = 0.00125: 64000 steps, 64001 force rows from t = 100,
  single forces directory, last time 180.
- A log scan for nan / FOAM FATAL / FOAM Warning / floating point matches
  only the header line "sigFpe : Enabling floating point exception
  trapping" in the two medium runs at dt 0.0025 and 0.00125, so those runs
  ran with FPE trapping on and did not abort.

## What the data supports
1. St is insensitive to mesh (0.07 %) and time step (0.02 %) at the
   medium -> fine / halved-dt level. No convergence order is claimed.
2. Cd mean varies by 0.12 % across the three meshes and 0.07 % across the
   last time-step halving; mesh increments are not monotone in size, so no
   error estimate by extrapolation is made.
3. Cl amplitude and Cl rms are not mesh-converged. If the observed rate
   (p about 0.9) continued, the fine mesh would still be roughly 4 - 5 %
   below the mesh-independent value and the medium mesh roughly 6 %.
   This is an extrapolation from three points and is an estimate only.
4. The time-step error converges more slowly than second order. The
   reason is not established. A first-order splitting error of the
   pressure-velocity coupling (two correctors, one outer iteration) is
   the working hypothesis and is untested.

## Inputs to the validation rule (note 02), not a verdict
Mesh term (medium -> fine) and time-step term (dt 0.0025 -> 0.00125 on
medium), % of the finer value:
St 0.070 and 0.018; Cd 0.092 and 0.066; Cl rms 1.635 and 0.63.
Domain-size term: not yet measured. Supplementary (not part of the rule):
extrapolated Cl rms mesh error roughly 4 - 5 % (finding 3).

## Limitations so far
- Whether the time-step error depends on the mesh is untested (fine mesh
  run at dt = 0.0025 only).
- Mesh levels were generated separately; wall-boundary-layer resolution
  scales with the level, so refinement is not a pure cell-size change.
- Only Re = 100 so far.

## Open items
- Domain-size study (copy the mesh, do not regenerate).
- Re = 150 through the same pipeline.
- Decision on the production mesh for the coupled stage (Cl not converged).
- Test of nOuterCorrectors > 1 on the time-step order, at the FSI stage.
- force_signal.py: add a plausibility warning, and apply --t1 to the
  per-cycle table.

## Reproducing the dt = 0.00125 case
cases/fixed_Re100_medium_dt0.00125 has startFrom latestTime and
startTime 0. It was restarted from the t = 100 state (time directory 100)
of cases/fixed_Re100_medium_dt0.0025. Time directories are not tracked, so
the committed case alone does not reproduce the run: without that directory
it would integrate from t = 0 to 180. Its forces are in
postProcessing/forces/100/forceCoeffs.dat.
