# Validation at 35° slant (corrected case)

*Part of [Project 01: Ahmed body](../README.md). Companion to
[validation-25deg.md](validation-25deg.md). Corrections to earlier work are listed in
[errata.md](errata.md).*

## 1. Purpose and short answer

At 25° the measured flow over the slant stays attached and the wake recirculation ends
between 188 and 238 mm behind the body. At 35° the measured flow separates over the
slant and the recirculation is longer. This document asks two things:

1. Does the corrected set-up reproduce that change, judged against criteria fixed before
   the 35° run?
2. How does the CFD flow differ between 25° and 35°?

**Short answer.** The 35° run reached a stationary state only after the averaging window
was restarted. Against the ERCOFTAC centreline data it passes three of the four
qualitative criteria and fails one: it does not reproduce reversed flow at the farthest
wake station. The pooled velocity error is 0.1529, which the criteria classify as poor,
and it is higher than at 25° (0.1020). The CFD-only comparison shows a larger,
slant-attached recirculation at 35° and a drag coefficient 3.5 % higher than at 25°. That
increase is **not verified**: there is no mesh-independence study, no measured 35° drag
to compare with, and two angles cannot show a trend.

## 2. Reference data and what is shown

Comparison data are ERCOFTAC Classic Collection AC1-05, Experiment 2, 35° configuration
(laser-Doppler anemometry, 40 m/s, symmetry plane y = 0):
<https://kbwiki.ercoftac.org/w/index.php/Test_Data_AC1-05>.

As for the 25° case, the data are © ERCOFTAC 2004 with no stated redistribution terms.
They are not in this repository, and no figure here shows measured points. Only
pass/fail outcomes, pooled error metrics and qualitative statements appear below. The
figures in this document are CFD-only.

## 3. Case set-up

| Item | Value |
|---|---|
| Geometry | Ahmed body, 35° rear slant, 50 mm ground clearance, half model with symmetry plane at y = 0 |
| Reference area | 0.056016 m² (half of the 0.112032 m² full-body value) |
| Inlet speed | 40 m/s |
| Solver | steady SIMPLEC (`foamRun`, `incompressibleFluid`), k–ω SST with wall functions |
| Mesh | 2,706,513 cells |
| Averaging | `fieldAverage1` (mean and prime2Mean of U, p, k) |

The 35° geometry was made from the 35° surface by `surfaceTransformPoints`, translating
by (0 0 0.05). The same command reproduces the 25° surface byte for byte. The mesh built
inside the reproducibility driver run has the same checksums as the separately built
mesh case, so the mesh can be regenerated exactly.

The inlet turbulence is the same as for the 25° baseline: free-stream turbulence
intensity 0.25 % and νt/ν = 10 at the nose (see [validation-25deg.md](validation-25deg.md)).

## 4. Reaching a stationary state

Stationarity was judged with the criterion used for 25°. A window passes when the drift
of Cd over the window, divided by the sample standard deviation (|drift/std|), is below
0.5 **and** the spread between four sub-window means is below 2 %.

| Window (iterations) | Mean Cd | Std of Cd | drift/std | Sub-window spread | Verdict |
|---|---|---|---|---|---|
| 1000–2000 | 0.29966 | 0.01734 | −1.245 | 5.7–7.0 % | **fails** |
| 2000–3000 | 0.29687 | 0.00923 | −0.006 | 0.05–0.16 % | passes |

In the first window the first fifth of the iterations (1000–1200) averages 0.31558,
while the other four fifths average 0.29479–0.29634. The solution was therefore still
relaxing early in the window, and the mean fields include that transient. The thresholds
were not changed after seeing this.

Averaging was restarted instead. The averaging files from iteration 2000 were set aside,
the run was continued for 1000 more iterations with `restartOnRestart yes`, and the
restart was checked by confirming that exactly 1000 iterations had been averaged at
iteration 3000. All 35° results below use the 2000–3000 window. The mean Cl in that
window is 0.11892. The 1000–2000 window stays on record as a failed first attempt.

This restart was carried out by hand. The driver now has a `--stage3-end` option that
automates it (see [reproducibility.md](reproducibility.md)), and its mechanics were tested
on a short run. The full 35° stage 3 has **not** been re-run through the driver.

## 5. Criteria and results

The 35° criteria were stated on 2026-10-11, before the run. They adapt the 25° criteria
to the measured 35° flow. The measured data show reversed flow over the slant from
x = −143 mm (2 points), growing to 14 points at x = −3 mm, and reversed flow in the wake
through x = 287 mm (11 points) but none at x = 337 mm.

| ID | Criterion | Result |
|---|---|---|
| C2′a | Reversed flow at every measured slant station from x = −123 to −3 mm | **pass** |
| C2′b | First reversed station in {−163, −143, −123} mm (measured onset: −143) | **pass**: first reversed station −123 mm |
| C3′a | Reversed flow at all wake stations (17, 37, 87 mm, and 137, 187, 237, 287 mm) | **fail**: none at 287 mm |
| C3′b | Recirculation end within 50 mm of the measured end (measured: between 287 and 337 mm), i.e. inside (237, 387] mm | **pass**: CFD ends in (237, 287] mm |
| C4′ | Normalised RMS error of U and W over slant and wake points: ≤ 0.05 good, 0.05–0.10 fair, > 0.10 poor | 0.1529, **poor** (n = 599) |
| C5 | Free-stream turbulence: report only | measured free-stream k about 8 times the CFD value |
| C1′ | Full-body drag | no verdict (no measured 35° drag) |

**Details.**

- **Onset of reversal (C2′b).** The CFD starts reversing one station later than the
  experiment. At x = −143 mm the CFD velocity is +7.55 m/s against −2.54 m/s measured.
  Over the slant stations the CFD has 61 reversed points against 78 measured.
- **Wake stations (C3′a).** Reversed points at x = 137, 187 and 237 mm: CFD 13, 10, 5;
  measured 17, 17, 15. At 287 mm the CFD has none, the measurement has 11.
- **Strength of the reversal.** Close to the base the CFD reversal is stronger than the
  measured one (minimum U −10.61 against −7.71 m/s at 37 mm, and −15.79 against
  −12.87 m/s at 87 mm). Farther downstream it is much weaker (−1.69 against −12.27 m/s at
  237 mm). The model's recirculation is shorter and more concentrated than the real one.
- **Tolerances.** C3′a requires reversal at every listed station, with no allowance,
  while C3′b allows 50 mm. A recirculation that ends one station early therefore fails
  C3′a and still passes C3′b. The criteria were not re-scored after seeing this.
- **Pooled error (C4′).** The errors are 0.1460 over the slant points (n = 149) and
  0.1551 over the wake points (n = 450). At 25° the corresponding values were 0.1852 and
  0.0667. The slant error is slightly better at 35° and the wake error is more than twice
  as large.
- **Free-stream turbulence (C5).** The measured free-stream k is 0.12–0.13 m²/s², the CFD
  value 0.015–0.017 m²/s², as at 25°. At 25° a test with higher inlet turbulence
  (Tu 0.5 %) improved the pooled error from poor to fair. That test was **not** repeated
  at 35°.

The hypothesis recorded before the run was that C2′ and C3′a would pass and that the end
of the recirculation was at risk. C2′ passed as expected. C3′a failed, and the failure is
the recirculation ending earlier than measured.

## 6. 25° versus 35° (CFD only)

Everything in this section compares two of our own simulations. It says nothing about
accuracy, only about how the model's flow differs between the angles.

**Reversed flow.** Values are from the y ≈ 0 plane.

| Angle | Wake reversed extent (m) | Wake reversed area (m²) | Reversed area on the slant (m²) | Minimum Ux/U∞ |
|---|---|---|---|---|
| 25° | 0.1879 | 0.01472 | 0.00000 | −0.336 |
| 35° | 0.2401 | 0.03204 | 0.00549 | −0.401 |

At 25° the slant carries no reversed flow in the CFD. At 35° a recirculation attached to
the slant appears, and the wake recirculation is longer (by about 52 mm) and covers more
than twice the area.

**Pressure drag by region.** Faces are split by position along the body. Friction is
obtained by difference from the total Cd given by `forceCoeffs`.

| Region | 25° Cd contribution | 35° Cd contribution |
|---|---|---|
| Front (x < 0.10 m) | −0.01432 | −0.01370 |
| Middle (0.10 m to slant start) | 0.00041 | 0.00098 |
| Slant | 0.14571 | 0.14970 |
| Base (rear face) | 0.10656 | 0.11474 |
| Other (beyond the slant) | 0.00142 | 0.00109 |
| **Pressure total** | **0.23979** | **0.25281** |
| Friction (by difference) | 0.04693 (16.4 %) | 0.04406 (14.8 %) |
| **Total Cd** | **0.28672** | **0.29687** |

The slant and the base together carry about 88–89 % of the total in both cases. The
front and underside contributions are nearly unchanged, and the underside minimum Cp is
−1.419 at x = 0.082 m in both cases, so the upstream flow is the same. The suction
minimum on the roof and slant is weaker at 35° (−1.953 against −2.775). The base
contribution rises by 0.008 and the slant contribution by 0.004, which together account
for most of the 0.013 rise in pressure drag. The rear-face area is smaller at 35°
(0.03134 m² against 0.03772 m²), so the larger base contribution means a lower mean base
pressure, not a larger face.

**Figures**

| | |
|---|---|
| Pressure coefficient, 35° symmetry plane | ![Cp at 35°](../results/val35_clr50/case_40ms/slice_val35_40ms_Cp.png) |
| Ux/U∞, 35° symmetry plane | ![Ux at 35°](../results/val35_clr50/case_40ms/slice_val35_40ms_Ux_over_Uinf.png) |
| Ux/U∞, 25° against 35° | ![Ux 25 vs 35](../results/val35_clr50/comparisons/ux_25_vs_35.png) |
| Centreline Cp, 25° against 35° | ![Centreline Cp](../results/val35_clr50/comparisons/centreline_cp_25_vs_35.png) |

Pressure in the slice figures is referenced to the outlet pressure. The decomposition
table uses a reference pressure taken from an upstream probe (x = −1.2 m), so the two Cp
conventions differ by a small constant (about 0.02) and should not be compared
number-for-number.

## 7. Interpretation

The CFD shows a change in flow topology that goes with the drag change, within the limits
in section 8. At 35° a recirculation forms on the slant and merges with the wake, which
lengthens and widens it. The roof-and-slant suction is weaker, yet the slant region
carries slightly more pressure drag, and the base sits at a lower mean pressure. Both
raise the drag. This document does not isolate why the slant contribution grows even as
its suction weakens. That would need the slant pressure integrated by facet, and we did
not do it.

The 35° result should not be read as a drag trend. In the classical Ahmed experiments the
drag coefficient peaks near 30° and falls at larger angles once the flow has detached from
the slant. Our 35° drag is higher than our 25° drag, so the CFD does not obviously show
that fall. We have no measured 35° drag in this project to compare with, two angles
cannot locate a peak, and we did not investigate the apparent difference further. It is
recorded here as an open point.

## 8. Limitations

- **No mesh-independence study.** Verification at both angles rests on one mesh, so the
  numerical error on Cd, on the reversed-flow extents and on the error metrics is unknown.
- **Two angles only.** The 25°/35° differences are a comparison, not a trend.
- **No verified 35° drag.** The 35° Cd is not compared with a measured value.
- **Poor pooled error.** C4′ = 0.1529 is rated poor by the criteria set in advance, and the
  wake error is larger than at 25°.
- **Recirculation shorter than measured.** The CFD wake reversal is too strong near the
  base and too weak downstream, and the criteria's two tolerances (C3′a and C3′b) give
  different verdicts on it.
- **Free-stream turbulence mismatch.** The measured free-stream k is about 8 times the CFD
  value (C5), and the turbulence test done at 25° was not repeated.
- **Steady RANS.** The model cannot represent unsteady shedding from the slant or the
  base. Stationarity shows that the mean forces settle, not that the flow is steady in
  reality.
- **Stage 3 done by hand.** The restarted averaging was run manually, not through the
  driver.

## 9. Reproducing

The case set-up, the stage-3 restart and the comparison scripts are described in
[reproducibility.md](reproducibility.md). The outcomes in this document come from the
stationarity, comparison and decomposition scripts under `scripts/` and
`scripts/validation/`, run on the 2000–3000 averaging window.
