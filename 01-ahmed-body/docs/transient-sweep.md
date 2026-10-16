# Transient sweep, 0° to 35° slant (exploratory)

*Part of [Project 01: Ahmed body](../README.md). The corrected, quantitatively checked
work is in [validation-25deg.md](validation-25deg.md) and
[validation-35deg.md](validation-35deg.md). Corrections E1–E7 are explained in
[errata.md](errata.md).*

## 1. What this document is

Before the validation cases existed, the project ran a series of steady and transient
RANS simulations at five slant angles (0°, 10°, 20°, 30°, 35°) plus 25°, to see how the
wake changes with the slant angle. This document records what was run and what came out.

**Status of the results.** The sweep is **exploratory and not validated**. Later checks
found problems that affect every number in it (section 6): the force coefficients are
half-body values, five of the six cases have no ground clearance, and the inlet
turbulence is about 5 %, far above the experiments. The sweep therefore cannot support
quantitative claims about the Ahmed body, about drag against slant angle, or about
shedding frequencies. It is kept because it documents the method and the difficulties
met (section 5), and because its qualitative observations suggested what the validation
cases should examine.

## 2. Set-up

| Item | Value |
|---|---|
| Geometry | Ahmed body, L = 1.044 m, W = 0.389 m, H = 0.288 m, 100 mm nose fillet (an approximation of the real nose) |
| Domain | half-domain with a symmetry plane at y = 0; 2L upstream, 6L downstream, 1L half-width, 2L high; stationary no-slip floor; slip walls on top and side |
| Inlet speed | 60 m/s (Re_L = 4.18 × 10⁶) |
| Turbulence model | k–ω SST with wall functions (`nutkWallFunction`, `kqRWallFunction`, `omegaWallFunction`) |
| Inlet turbulence | k = 13.5 m²/s², ω = 91.79 s⁻¹ (about 5 % intensity; assumed, see E4) |
| Steady solver | SIMPLEC, `residualControl` 10⁻⁴ |
| Transient solver | PIMPLE, maximum Courant number 0.5, 8 MPI ranks |
| Meshing | `snappyHexMesh`, no boundary-layer prisms |
| Force coefficients | `forceCoeffs` with Aref = 0.112032 m² (full frontal area) on the half body (E1) |

**Wall treatment.** A wall-resolved mesh (y⁺ ≈ 1 with extruded layers) was attempted
first. It failed at the two rear trihedral corners, where layer extrusion collapsed,
for every layer count, mesh size and feature setting tried (summary in
[development-log.md](development-log.md)). The project then used wall functions with
surface refinement only. An analytic estimate put the wall-adjacent cells at
y⁺ ≈ 97–194 for the finest steady mesh. The validation case on a mesh of the same
refinement level later gave a *measured* y⁺ of 17.9–116.5 on the slant at 40 m/s (median
43.8), so the analytic estimate was higher than the measured values. The difference is
not fully explained by the lower speed, and y⁺ was never measured in the sweep itself.

**Mesh sizes.** Steady 25° baseline: 2,725,204 cells at refinement level (6,7). To keep
the transient runs affordable (about 2.4 s per time step at 25°), transient meshes were
coarsened to level (4,5): 872,391 cells at 25°, 847,879 at 10°, 849,762 at 20° and
844,113 at 35°. The 30° case used level (5,6) with 1,121,804 cells, so its mesh is
finer than the others. No mesh-independence study was done at any angle.

## 3. Results

Values are as reported at the time, **half-body** (E1). The last column doubles Cd for
the half-body correction; Cl is affected in the same way. Windows differ from case to
case.

| Slant | Case | Window | Cd (reported) | Cd × 2 | Cl (reported) | Wake frequency result |
|---|---|---|---|---|---|---|
| 0° | steady | iterations 1200–2000 | 0.15141 (std 0.00186) | 0.3028 | not recorded here | limit cycle of about 22.5 iterations (no physical meaning) |
| 0° | transient to 0.45 s | not stationary | not recorded here | | | inconclusive; inter-peak periods varied with CoV 46–48 % |
| 10° | transient to 0.35 s | 0.13–0.35 s | 0.1433 (std 0.0044) | 0.2866 | 0.5986 (std 0.0032) | no single frequency; amplitude-modulated bursts |
| 20° | transient to 0.2 s | not evaluated | not recorded here | | | inconclusive; 4 robust peaks, CoV 43 %, no St reported |
| 25° | steady | iterations 1000–2000 | 0.1528 (std 0.0017) | 0.3056 | not recorded here | limit cycle of 17.26 iterations (no physical meaning) |
| 25° | transient to 0.20 s | 0.06–0.20 s | 0.1619 (std 0.0039) | 0.3238 | 0.1204 (std 0.0500) | about 65.4 Hz in Cd, Cl and a wake probe |
| 30° | transient to 0.2 s | 0.06–0.20 s | 0.1629 (std 0.0057) | 0.3258 | 0.7615 (std 0.0067) | continuous multi-scale fluctuation, no plateau, no St reported |
| 35° | transient to 0.30 s | 0.14–0.30 s | 0.1589 (std 0.0030) | 0.3178 | 0.7146 (std 0.0026) | peak near 60 Hz, but the pre-set criterion was not met |

Two features of the table need a comment. First, the 25° Cl (0.12) is about six times
smaller than the Cl at 30° and 35° (0.71–0.76). Only the 25° case has the 50 mm ground
clearance (E2), so the underbody flow differs, and this probably explains most of the
difference. It was not isolated. Second, the 0°, 10° and 20° rows are incomplete
because their statistics were never collected in one place, and I have not reconstructed
them.

**Figures (25° and 0° only; the other angles have figures in the old README).**

| | |
|---|---|
| 25° steady Cd history and its spectrum | ![25° steady Cd](../results/slant25_re4.29M/steady_cd_fft.png) |
| 25° transient Cd trajectory | ![25° transient Cd](../results/slant25_re4.29M/transient_cd_trajectory.png) |
| 25° wake recirculation, 7 frames | ![25° wake sequence](../results/slant25_re4.29M/wake_recirculation_sequence.png) |
| 0° velocity snapshot at t = 0.45 s | ![0° velocity](../results/slant00_re4.18M_transient/velocity_snapshot_t0.45.png) |

## 4. Case notes

**0°.** The steady solve did not converge to a fixed point: Cd settled into a limit cycle
of about 22.5 iterations. A transient run to 0.45 s gave an irregular signal. After
progressively longer windows the variability of the peak spacing did not fall (CoV
46–48 %), unlike at 25°. A single snapshot shows a recirculation region with Ux down to
−30 m/s coinciding with a low-pressure core. Only two time steps survived near the end
of the run, so no wake evolution was shown.

**10°.** The record shows bursts of oscillation separated by quiet periods rather than a
single frequency. The mean values above span that modulation, so they are not statistics
of a settled state. The steady check was only 300 iterations.

**20°.** Peak detection at the default prominence picked up solver-step noise
(28 "peaks" about 12 µs apart). A sweep of the prominence threshold gave a stable set of
four genuine peaks, with intervals of 0.0115, 0.0343 and 0.0199 s (CoV 43 %). That is too
few and too irregular to define a frequency, and the run was not extended (stage 1 alone
took about 19.8 hours).

**25°.** The steady solve gave a clean limit cycle (17.26 iterations; Cd 0.1528 ± 0.0017).
The transient run reached stationarity in Cd by about 0.06 s, with a dominant frequency
of about 65.4 Hz (peak-to-peak periods 0.01523 s and 0.01538 s in two sub-windows), and a
wake probe gave 65.57 Hz. The Cl record still drifted by about 10 % over the window, so
the Cl statistics are less trustworthy than the Cd statistics. Over the window Cd ranged from
0.1563 to 0.1698 (four sub-window means 0.1606–0.1628) and Cl from 0.0492 to 0.1936. In height-based form
f·H/U∞ = 65.4 × 0.288 / 60 ≈ 0.31. This St is arithmetic only: the literature
comparison that accompanied it in the old README was not supported (E5).

**30°.** The Cd trace contains structure on several amplitude scales at once. The
peak-count sweep never settled (11 peaks falling smoothly to 2 as the threshold rose), so
no frequency was defensible. This case used the finer (5,6) mesh, so its different
character may come partly from the mesh. A (4,5) rerun to check that was never done.

**35°.** The primary window had a Cl mean of 0.7146 with a very small spread. The
frequency analysis found Cd, a pressure probe and two velocity components peaking near
60 Hz. The pre-set criterion required the Cd peak to stand out by a factor of 5 over the
background, and in the longer window it reached 4.7, so the criterion was not met and no
Strouhal number was reported. The corrected 35° case in
[validation-35deg.md](validation-35deg.md) replaces this case for any quantitative use.

## 5. What can and cannot be concluded

**Reasonable to say.** In these RANS runs the force signals at the six angles behave
differently: monotonic decay with noise at 0°, bursts at 10° and 20°, multi-scale
fluctuation at 30°, and a narrow peak near 60–65 Hz at 25° and 35°. Steady SIMPLEC at 0°
and 25° does not converge to a fixed point in this set-up.

**Not established.**

- *That no steady solution exists* (E7). The old README concluded this from the steady
  limit cycles plus the transient runs. The evidence shows that this solver in this
  configuration did not converge. It does not exclude a steady solution with different
  numerics, a finer mesh or lower inlet turbulence. At 25°, the later corrected steady
  runs also settled into limit-cycle-like histories, and the stationarity analysis in the
  validation documents treats such histories by averaging.
- *That the 65 Hz oscillation is a real physical phenomenon* (E7). The agreement between
  Cd, Cl and a wake probe (0.33 %) is internal consistency within one run on one coarse
  mesh. It does not show that the real flow has a 65 Hz mode.
- *Identification of "bubble pumping" or any other mechanism.* This relied on literature
  that was not verified (E5) and on seven frames of one run.
- *Any trend with slant angle.* Windows, durations, mesh levels and ground clearance
  differ between cases.

## 6. Corrections that apply to every number above

| ID | Effect on the sweep |
|---|---|
| E1 | Cd, Cl and Cm are half-body values. Multiply by 2 for the full body. |
| E2 | The body rests on the floor at 0°, 10°, 20°, 30° and 35°. Only 25° has the 50 mm clearance, so the cases are not geometrically comparable. |
| E4 | Inlet turbulence is about 5 % intensity (assumed; viscosity ratio near 9,800), not the 0.25 % of the reference experiment. Heavy eddy viscosity may suppress unsteadiness; the effect was not tested in the sweep. |
| E5 | The Strouhal-number literature check is unsupported. |
| E6 | `resolveFeatureAngle` and `includedAngle` were treated as one setting. The meshes differ in curvature refinement from angle to angle, which weakens cross-angle comparison. |
| E7 | The conclusions "no steady solution" and "the oscillation is physically real" were stronger than the evidence. |

For comparison with the corrected work: the 25° sweep Cd, doubled for E1, is 0.3238, and
the corrected 25° validation value is 0.28672. The two differ in speed (60 against
40 m/s), inlet turbulence, mesh, averaging method and Tu, so their difference should not
be attributed to any single cause.

## 7. Where the material is

The full chronological record of the sweep is in the old README, available as
`git show pre-docs-rewrite:01-ahmed-body/README.md`, and the mesh work is in
[development-log.md](development-log.md). Raw solver output is not in the repository.
The case dictionaries are under `cases/` and the figures under `results/slant*`.
