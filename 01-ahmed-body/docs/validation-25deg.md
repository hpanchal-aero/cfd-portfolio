# Validation Case: 25° Slant, 50 mm Clearance, Compared with ERCOFTAC AC1-05

**Question.** Does a corrected setup (25° slant, 50 mm ground clearance, half-body
reference area, inlet turbulence matched to the experiment) reproduce the flow measured
behind and over the slant of the Ahmed body?

**Answer in short.**

- The wake recirculation is reproduced: the number of reversed-flow points behind the
  base and the end of the recirculation agree with the measurement (criteria C3).
- The slant boundary layer is not reproduced: about 15 mm above the slant the computed
  speed is 1.5–2.6 times the measured one (criterion C4, slant-only "poor").
- The accuracy of the computed drag is not established. The source paper prints no 25°
  drag value, so criterion C1 received no pass/fail verdict.
- There is no mesh-independence or wall-treatment study, so no comparison carries an
  uncertainty estimate and model error cannot be separated from numerical error.

This is the first and only quantitative comparison with experimental data in Project 01.
It concerns the case family `cases/val25_clr50_*`, not the transient sweep
([transient-sweep.md](transient-sweep.md)), whose cases are subject to the corrections in
[errata.md](errata.md). The same procedure applied to a 35° slant is in
[validation-35deg.md](validation-35deg.md).

## 1. Purpose, criteria and reference data

Criteria C1–C5 were fixed before any run. The comparison data are ERCOFTAC Classic
Collection AC1-05, Experiment 2 (Lienhart et al.; laser-Doppler anemometry, 40 m/s,
symmetry plane y = 0): <https://kbwiki.ercoftac.org/w/index.php/Test_Data_AC1-05>.

The ERCOFTAC page marks the data "(c) copyright ERCOFTAC 2004" and states no licence or
redistribution terms. Permission to redistribute has not been obtained, so the measured
data are **not** in this repository and **no figure here shows measured points**. Only
pass/fail outcomes, pooled error metrics and qualitative statements are reported. See
`validation/reference_data/README.md` for how to obtain the data and run the comparison
locally.

## 2. Cases

| Case | U∞ [m/s] | Re_L | Nose Tu, νt/ν (design → sampled in the solution) | Inlet k0, ω0 |
|---|---|---|---|---|
| `val25_clr50_40ms` (**headline**) | 40 | 2.784e6 | 0.25 %, 10 → 0.253 %, 10.09 | 0.027751, 176.1 |
| `val25_clr50_60ms` | 60 | 4.176e6 | 0.25 %, 10 → 0.255 %, 10.09 | 0.1051, 639.8 |
| `val25_clr50_40ms_tu05` (**sensitivity test**) | 40 | 2.784e6 | 0.5 %, 20 → 0.522 %, 20.35 | 0.52657, 1475.3 |

- **Geometry.** The 25° STL with 50 mm clearance (z = 0.05 to 0.338 m), a half domain with
  a symmetry plane at y = 0, and Aref = 0.056016 m² (half of the 0.112032 m² frontal
  area), so the coefficients below equal full-body coefficients.
- **Mesh.** snappyHexMesh, refinement levels (6,7), `nCellsBetweenLevels 3`, a uniform wake
  box at level 3, 2,725,204 cells. `checkMesh` passes: maximum aspect ratio 3.42, maximum
  non-orthogonality 32.9° (average 7.85°), maximum skewness 0.953 (the highest in the
  project; its location was never found). The mesh is the same in all three cases (the
  `polyMesh` files are byte-identical).
- **Solver.** OpenFOAM 11 `foamRun` with the `incompressibleFluid` solver, steady SIMPLEC,
  k–ω SST with wall functions (`nutkWallFunction`), numerical settings copied from the
  frozen 25° case, 8 MPI ranks, 2000 iterations. Mean fields (U, p, k and second moments)
  are iteration-averaged with `fieldAverage` over iterations 1001–2000.
- **Inlet turbulence.** Set from the free-stream SST decay relation (β = 0.0828,
  β* = 0.09) so that the nose has the target Tu and νt/ν. The values in the table were
  checked by sampling the converged fields near the nose
  (`scripts/validation/check_nose_turbulence.py`).
- **The tu05 case changes two variables at once** (turbulence intensity and viscosity
  ratio), because a nose Tu of 0.5 % is not reachable at ratio 10 with this decay relation
  at 40 m/s. Any difference to the baseline therefore cannot be attributed to one of them.
- **Run history.** The baseline stage 1 was stopped at iteration 312 to free CPU cores and
  continued (313–1000). The tu05 stage 1 was interrupted at iteration 90 and resumed from
  the iteration-50 write, so the log of iterations 1–90 was overwritten; the force history
  of that segment survives. Stage 2 (1001–2000, with `fieldAverage`) ran without
  interruption in all cases. Force histories were stitched from the restart segments, later
  segments winning on overlaps; there are no gaps.

## 3. Convergence and stationarity

The pre-stated criterion for the averaging window is a drift/std of Cd below 0.5 in
magnitude and a four-window spread of the window mean below 2 %. It was calibrated on the
baseline's own stage-1 history, where it first holds for windows starting at iteration 700.

| Case | Cd mean (1000–2000) | Cd std | Cl mean | Cl std | drift/std | 4-window spread |
|---|---|---|---|---|---|---|
| 40 m/s | 0.28672 | 0.00308 | 0.32051 | 0.07547 | 0.118 | 0.095 % |
| 60 m/s | 0.28864 | 0.00295 | 0.31823 | 0.07457 | 0.00 | 0.02 % |
| 40 m/s, tu05 | 0.29500 | 0.00291 | 0.32633 | 0.07326 | 0.016 | 0.059 % |

All three pass. The residuals do **not** reach the 10⁻⁴ target: in the baseline the final
U_z residual is of order 2×10⁻², and the Cl histories oscillate in a limit cycle (std about
0.07 in all cases; the period was not measured). This is an oscillation in the iteration
count of a steady solver, not a physical frequency. The means above are means over that
oscillation, not converged steady values. The residual histories of the 60 m/s and tu05
cases were not separately examined.

![Force histories of the three cases](../results/val25_clr50/comparisons/force_history_3cases.png)

## 4. Criteria and results

| ID | Criterion | Baseline (Tu 0.25 %) | tu05 (Tu 0.5 %) |
|---|---|---|---|
| C1 | Full-body Cd against Experiment 1 (Ahmed 1984, 60 m/s): ≤ 10 % agree, 10–20 % partial, > 20 % disagree | **no verdict** (see below) | not applicable |
| C2 | No reversed flow above the slant at the measured stations | pass | pass |
| C3a | Reversed flow at the wake stations 38, 88 and 138 mm | pass (10/8/6 points against 8/7/6 measured) | pass |
| C3b | Recirculation end inside 138–288 mm | pass: ends in (188, 238] mm, the measured interval | pass: same interval |
| C4 | Normalised RMS error of U and W over slant and wake points: ≤ 0.05 good, 0.05–0.10 fair, > 0.10 poor | 0.1020, **poor** (n = 562) | 0.0960, **fair** |
| C5 | Upstream floor layer and modelled k: report only | see text | see text |

**C1: no pass/fail verdict.** Ahmed et al. (1984), SAE 840300, prints the drag coefficient
Cw only at 0° (0.250), about 12.5° (0.230) and 30° (0.378 for the high-drag case, 0.260 for
the low-drag case) in its Fig. 4. **No 25° value is printed**, and the numeric reference
area F is not stated. Two graph readings (approximate, read by eye from the figures, not
printed values) disagree with each other: Fig. 4 gives Cw ≈ 0.285 at 25° (±0.005), and
Fig. 15(e), a second drag-versus-slant curve (0.272 at 0°, 0.33 at 30°), gives about 0.25
at 25°. The paper does not explain the difference. Against these, the computed 60 m/s Cd of
0.2886 is about +1 % (Fig. 4) or about +15 % (Fig. 15e); the 40 m/s value 0.2867 is about
+1 % and +15 %. The pre-stated bands would therefore give "agree" or "partial" depending on
which figure is trusted, so **no verdict is assigned**. The comparison is further limited
because the experiment used stilts with a tare correction and an open test section (the CFD
has neither), F is not stated, and the experiment is at Re 4.29e6 against 4.18e6 for the CFD
at 60 m/s. A close total Cd would not by itself indicate a correct flow field: the slant
boundary layer is not reproduced.

**C2 caveat.** The lowest measured point above the slant is about 14–15 mm from the surface,
so this check cannot see a thin bubble.

**C4 split.**

| | Baseline | tu05 | n |
|---|---|---|---|
| slant only | 0.1852 (poor) | 0.1698 (poor) | 112 |
| wake only | 0.0667 (fair) | 0.0659 (fair) | 450 |

The change of the pooled value from baseline to tu05 (poor to fair) is about 0.006 and
crosses the 0.10 threshold. It carries no uncertainty estimate and must not be read as a
validated improvement. The slant-only value is poor in both cases. The headline case is the
pre-registered baseline; tu05 is a sensitivity test and does not replace it.

**C5 (report only).** In the baseline, the modelled turbulence kinetic energy in the upstream
floor layer and in the free stream is far below the level implied by the measurement
(measured free-stream k about 5.6–7.8 times the computed value). tu05 raises it to the same
order, but the free-stream level stays below the measurement-implied one. The upstream
floor-layer velocity error changes little between the cases.

## 5. What agrees and what does not

**Agrees:** no reversed flow above the slant, and a recirculation behind the base whose
extent falls in the measured interval (C2, C3). The wake-only error is "fair" (0.067).

**Does not agree:** the velocity profiles over the slant. In the baseline the computed
boundary layer over the slant is thinner and much fuller than measured, with the divergence
beginning between the x = −163 mm and x = −143 mm stations (x measured from the rear base).
About 15 mm above the slant the computed speed is 1.5–2.6 times the measured one (31–42 m/s
against 13–28 m/s). tu05 reduces the profile error at all ten slant stations, by 4–11 % of the
baseline error, but the layer stays far too full. The discrepancy is therefore not removed by
the free-stream turbulence change tested here.

## 6. CFD-only slant-layer diagnostic

Iteration-averaged U [m/s] above the slant surface, with x measured from the rear base.

| Station x [mm] | Case | +1 mm | +5 mm | +10 mm | +15 mm | +20 mm | +30 mm |
|---|---|---|---|---|---|---|---|
| −143 | baseline | 21.6 | 28.0 | 37.3 | 42.4 | 44.0 | 44.9 |
| −143 | tu05 | 20.1 | 26.3 | 35.3 | 40.9 | 43.0 | 44.9 |
| −103 | baseline | 17.6 | 24.3 | 32.0 | 36.7 | 39.5 | 41.6 |
| −103 | tu05 | 15.8 | 22.2 | 29.7 | 34.7 | 38.1 | 41.2 |
| −63 | baseline | 15.7 | 21.4 | 28.5 | 34.8 | 37.7 | 40.2 |
| −63 | tu05 | 13.6 | 18.9 | 25.9 | 32.6 | 36.1 | 39.7 |
| −23 | baseline | 15.1 | 20.3 | 28.0 | 31.4 | 35.0 | 38.6 |
| −23 | tu05 | 12.5 | 17.4 | 25.0 | 28.7 | 32.9 | 37.8 |
| −3 | baseline | 15.6 | 19.1 | 25.0 | 30.8 | 33.8 | 37.8 |
| −3 | tu05 | 12.6 | 16.0 | 21.8 | 27.8 | 31.4 | 36.8 |

- About 10–11 distinct cells span the first 30 mm above the slant.
- Wall-function y⁺ on the slant (baseline / tu05): minimum 17.9 / 16.5, median 43.8 / 42.6,
  maximum 116.5 / 115.9; 73.3 % / 72.7 % of slant faces lie in the 30–300 band, 26.7 % / 27.3 %
  below 30 and none above 300. About a quarter of the slant wall-adjacent cells therefore sit
  below the usual wall-function range.

## 7. Drag decomposition (CFD only)

Pressure drag by region, as Cd on Aref = 0.056016 m². Pressure is referenced to an upstream
free-stream probe at x = −1.2 m, y = 0.05 m, z = 0.70 m.

| Region | 40 m/s | 60 m/s | 40 m/s tu05 | 60 − 40 | tu05 − 40 |
|---|---|---|---|---|---|
| front (x < 0.10) | −0.01432 | −0.01171 | −0.01005 | +0.00261 | +0.00427 |
| mid (0.10 to slant) | 0.00041 | 0.00041 | 0.00040 | +0.00000 | −0.00001 |
| slant | 0.14571 | 0.14456 | 0.14442 | −0.00115 | −0.00129 |
| base (rear face) | 0.10656 | 0.10672 | 0.10818 | +0.00016 | +0.00162 |
| other (x > slant) | 0.00142 | 0.00142 | 0.00139 | +0.00000 | −0.00003 |
| pressure total | 0.23979 | 0.24140 | 0.24434 | +0.00161 | +0.00455 |
| friction (by difference) | 0.04693 | 0.04724 | 0.05066 | +0.00031 | +0.00373 |
| Cd total (forceCoeffs, 1000–2000 mean) | 0.28672 | 0.28864 | 0.29500 | +0.00192 | +0.00828 |

"Friction" is the residual (total minus integrated pressure), not an integrated shear
stress. At the baseline the slant carries about half of Cd (50.8 %), the base about 37 %
(37.2 %) and friction about 16 % (16.4 %). The base-face mean Cp is −0.158 and the nose
stagnation value 0.989.

## 8. Flow fields

Same view (symmetry plane, y = 0.5 mm) and the same colour limits in every case. Here
Cp = 2·p̄/U∞², with the **outlet pressure** as reference; the centreline Cp figure and the
decomposition above use the upstream probe instead, and the two conventions differ by a
small constant. The fields are cell-centred and interpolated to points, so the coarse
upstream mesh appears blocky.

| | Cp | U_x/U∞ |
|---|---|---|
| 40 m/s | ![](../results/val25_clr50/case_40ms/slice_val25_40ms_Cp.png) | ![](../results/val25_clr50/case_40ms/slice_val25_40ms_Ux_over_Uinf.png) |
| 60 m/s | ![](../results/val25_clr50/case_60ms/slice_val25_60ms_Cp.png) | ![](../results/val25_clr50/case_60ms/slice_val25_60ms_Ux_over_Uinf.png) |
| 40 m/s, tu05 | ![](../results/val25_clr50/case_40ms_tu05/slice_val25_40ms_tu05_Cp.png) | ![](../results/val25_clr50/case_40ms_tu05/slice_val25_40ms_tu05_Ux_over_Uinf.png) |

![Centreline Cp, three cases](../results/val25_clr50/comparisons/centreline_cp_3cases.png)

The three cases are nearly indistinguishable in these views (root-mean-square difference of
the normalised 40 and 60 m/s slices: U_x/U∞ 0.022, Cp 0.0028). The suction spike at the
roof/slant edge (Cp near −2.7) sits at a geometric edge and its height depends on local mesh
resolution; no mesh study was done, so it carries no quantitative claim.

## 9. Physical interpretation

- The wake topology, a single recirculation bubble behind the base ending in the measured
  interval, is reproduced. The slant boundary layer is not: it is too thin and too full, so
  the model does not capture the slant-layer state that feeds the separation at the base.
- Going from 40 to 60 m/s changes Cd by +0.67 % and Cl by −0.71 %, with the largest change
  in the pressure drag of the front region and a slightly lower slant contribution.
- The Cd increase with tu05 (+0.00828) splits between pressure (+0.00455, nearly all of it in
  the front region) and the friction residual (+0.00373); slant and base nearly offset each
  other. It is not a separation-driven change. **Hypothesis, not tested:** the higher
  turbulence intensity and viscosity ratio change the boundary-layer development on the nose
  rounding, which weakens the suction there (the minimum slice Cp is −2.338 for tu05 against
  −2.450 for the baseline).

## 10. Engineering conclusions

- The model reproduces the position and extent of the recirculation behind this 25° Ahmed
  body. It should not be used for slant-layer or separation-onset predictions without
  further work.
- The accuracy of the computed drag is **not established**: the reference Cw at 25° exists
  only as a graph reading, the paper's two drag curves disagree there, and the experiment
  included stilts and a tare correction that the CFD does not model.
- Changing the inlet turbulence from 0.25 % to 0.5 % (with the viscosity ratio from 10 to 20)
  changes Cd by a few percent but does not repair the slant layer.

## 11. Limitations and untested hypotheses

- No mesh-independence or wall-treatment study (project decision), so model error cannot be
  separated from numerical error, and the C4 numbers carry no uncertainty estimate.
- Steady RANS with k–ω SST and wall functions. About a quarter of the slant wall-adjacent
  cells have y⁺ below 30. Whether wall resolution, the RANS/SST model, or both cause the thin,
  full slant layer is **untested**.
- The inlet turbulence is set from an analytic decay relation, and the fields at the nose
  differ slightly from the design values (0.522 % against 0.5 % for tu05).
- The tu05 case changes two variables together.
- The residuals are not converged (limit cycle), and the means average over the oscillation.
- Only the y = 0 plane files were used. Other planes, the rear-body wall pressure and the
  near-wall hot-wire data of Experiment 2 were not used.
- The numerical domain (blockage 2.57 %) does not model the three-quarter-open test section of
  the experiment, and the effect of the lateral and top boundary treatment was not tested.
- No stilts are modelled.
- Experiment 1 (drag, 60 m/s, Re 4.29e6) differs from the computed 60 m/s case (Re 4.176e6),
  and its reference area is not known to be the one used here.

## 12. Reproducing the case

The tracked case directories are `cases/val25_clr50_mesh` (the mesh, built from the frozen
25° STL), `cases/val25_clr50_40ms`, `cases/val25_clr50_60ms` and
`cases/val25_clr50_40ms_tu05` (same mesh; the inlet values are in
`0/include/initialConditions`). The driver script `scripts/validation/run_validation_case.sh`
runs the whole chain for one case in a fresh directory outside the repository; see
[reproducibility.md](reproducibility.md) for the commands and for what has and has not been
verified. In short, the 40 m/s baseline was rebuilt and reproduced the window statistics
(Cd 0.28672 and Cl 0.32051) and a byte-identical mesh, with iteration histories that are not
bit-identical. The 60 m/s and tu05 cases were not re-run through the driver.

## Revision notes

- Criterion C1 originally said the source paper had not been obtained. It was obtained
  (SAE 840300) and read; the C1 text above is the corrected account.
- The ERCOFTAC terms were checked on 2026-10-11: the page states only the 2004 copyright and no
  redistribution terms, so the data and any measured-data figure remain outside the repository.
