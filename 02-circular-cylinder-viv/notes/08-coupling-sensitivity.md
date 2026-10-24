# Note 08 -- coupling sensitivity of the free-vibration case (Re 150, U_r = 5)

Date: 2026-10-23 / 24.  Working note, to be rewritten into the final docs.

## Purpose
D10 = A: no separate forced-oscillation stage; the coupling is verified inside the FSI stage by
sensitivity runs of one free-vibration case. Note 07 left open which part of the strong-coupling
set-up is needed and how much the amplitude depends on it.

## Cases (all: Re 150, f_n = 0.2 (U_r = 5), m* = 2.546, zeta = 0, zones 1.5 / 10, restart from t = 100
of the fixed Re 150 reference, run to t = 130; the release run of note 07 is the baseline)
- baseline: Newmark, nOuterCorrectors 3, moveMeshOuterCorrectors yes, dt 0.0025
- coupling_Ur5_nO2: nOuterCorrectors 2
- coupling_Ur5_nO1: nOuterCorrectors 1 (moveMeshOuterCorrectors removed)
- coupling_Ur5_sym3: symplectic integrator, 3 outer correctors
- coupling_Ur5_dt0.00125: dt = 0.00125
Scripts: scripts/run/make_coupling_study.sh builds them; scripts/analysis/save_coupling_study.sh
regenerates results/feasibility/coupling_study_{body_motion_115-130,table}.txt and
coupling_sym3_divergence.txt.

## Result 1: the symplectic integrator diverges even with 3 outer correctors
- Floating-point exception in the GAMG pressure solve at t = 100.1275 (step 51, 33 s of run time).
- Spring length: 2.4e-5 (t = 100.015), 1.1e-4, 2.8e-4, 7.8e-4, 3.1e-3, 0.017, 0.093, 0.42 (t = 100.12),
  sampled every 6 steps: growth of about 30 % per step from the first steps.
- Together with the first failure of note 07 (symplectic, 1 outer corrector, stiff spring) this shows that
  the integrator was the deciding factor, which agrees with the source: the symplectic position update
  uses only the old acceleration, so outer correctors cannot strengthen the coupling. The mechanism
  (added mass or another) is not isolated; the statement is "explicit coupling through the integrator".
- Not run: Newmark with 1 outer corrector at the stiff spring (f_n = 10).

## Result 2: completed variants, window t = 115-130 (2 whole body periods, same script and window)
case                      f_body    A_y      mean x    mean Cd   Cl rms
baseline (nO3, dt 0.0025) 0.18845   0.5875   0.32685   2.0639    0.29379
nO2                       0.18898   0.5885   0.32810   2.0712    0.30189
nO1                       0.18916   0.5931   0.32979   2.0823    0.28381
dt 0.00125                0.18849   0.5874   0.32680   2.0636    0.29470
Differences against the baseline [%]:
nO2         f +0.281   A_y +0.170   mean x +0.382   Cd +0.355   Cl rms +2.757
nO1         f +0.377   A_y +0.953   mean x +0.899   Cd +0.889   Cl rms -3.397
dt 0.00125  f +0.021   A_y -0.017   mean x -0.015   Cd -0.015   Cl rms +0.310
- The x force balance closes to within 0.04 % in all four cases (criterion 3 %).
- Against the FSI floors of D11 (A_y* 5 %, frequency 2 %): the largest effects are 0.95 % (A_y) and
  0.38 % (f). Cl rms has no verdict; its spread is about 3 %.
- Run times (solver): nO1 1785 s, nO2 3010 s, dt/2 7000 s; the baseline took 6932 s for 60 time units,
  i.e. about 3470 s per 30 (assuming constant cost per step). Four runs shared the machine.

## Decision D12 = A
The U_r sweep uses Newmark, 3 outer correctors, moveMeshOuterCorrectors yes. One outer corrector is the
fallback if the sweep is too slow (stable here, about half the cost, differences below 1 % on the
verdict quantities).

## Limits
- Window of only 2 periods; the amplitude had not saturated (baseline y maxima 0.5882 at t = 125,
  0.5918 at t = 131, 0.5942 at t = 157), so the differences mix growth timing and the steady amplitude.
- The dt = 0.00125 case restarts from a state produced at dt = 0.0025; a small start-up transient is
  possible. Only one halving, so no order of convergence.
- One run per case, one U_r, one mesh and domain. Stability of nO1 is shown only at U_r = 5.
- Dependence on mesh and domain size is not tested in the FSI set-up.
