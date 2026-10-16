# Development log: meshing and the first transient run

*Part of [Project 01: Ahmed body](../README.md). This is a readable account of how the
original 25° case was meshed and run, including the dead ends. The full original notes
are in `mesh/mesh_development_log.md`. Corrections to claims made in those notes are
listed in [errata.md](errata.md) and applied here.*

## 1. Summary

The first goal was a wall-resolved mesh (y⁺ ≈ 1, 18 extruded boundary-layer cells).
Layer extrusion could not be made to work at the rear corners of the body, and the
last promising configuration crashed the WSL2 virtual machine at the layer-addition step.
The project switched to wall functions with surface refinement only, which produced a
mesh that passed all quality checks (2,725,204 cells). A steady SIMPLEC run on that mesh
did not converge to a point but settled into a periodic limit cycle, so a transient
PIMPLE run was set up. It needed two fixes, and then a coarser mesh to be affordable.
On the coarse mesh the Cd signal showed an oscillation near 65 Hz.

Everything quantitative in this document comes from the original set-up: half-body force
coefficients (E1), about 5 % inlet turbulence (E4) and no comparison with experiment.
Treat the numbers as a record of the method, not as results.

## 2. The wall-resolved attempt

The target was a layer stack with a first-cell thickness of 6.742 × 10⁻⁶ m, expansion
ratio 1.2 and 18 layers (total thickness 0.864 mm).

| Step | Change | Outcome |
|---|---|---|
| 1 | surface level (4 6), feature edges at level 6, `resolveFeatureAngle` 30 | no layers were added. Background cells near the wall (minimum volume 4.38 × 10⁻¹⁰ m³, about 0.76 mm edge) were as thick as the whole layer stack. |
| 2 | surface level (6 8) | castellation did not converge: over 7.1 million cells by iteration 72, with level-8 cells growing every iteration. Stopped by hand. |
| 3 | `resolveFeatureAngle` 60 | same failure |
| 4 | removed the explicit feature-edge block | same failure, ruling out that block |
| 5 | surface level (6 7) | used for the diagnostics below |

**Where the refinement was going.** An inspection of the surface mesh found that 132 of
the 142 flagged feature edges lay in the front fillet, where tessellation facets meet at
angles up to 90°, the same range as genuine sharp edges. This explained why the feature
block could not converge, but removing it did not cure the failure. A later spatial
analysis of the level-7 cells (taken from the stored cell levels) showed the real
concentration at the two rear side edges, where the slant edge, the side edge and the
rear face meet. A test with the wake refinement box removed gave an identical level-7
count (229,604 cells), so the box was not the cause.

**A rear-corner fillet was rejected.** Rounding the corners would have removed the
problem, but the standard Ahmed body has sharp rear edges and the validation target uses
that geometry. The original notes also cited rounded-edge studies (Thacker et al. 2012)
and a result that rear corner radius changes drag (Keogh et al.). Those citations came
from a literature search and were **not checked against the papers**, so the decision
stands on the geometry argument alone.

**`resolveFeatureAngle` sweep.** With castellation only (level (6 7)):

| `resolveFeatureAngle` | Result |
|---|---|
| 60 | plateau of about 90–220 cells per iteration, never converging |
| 90 | converged, but 205,832 level-7 cells remained |
| 120 | converged with zero level-7 cells |
| 170 | identical mesh to 120 (5,250,171 cells) |

The 90° value then **failed under full production settings** (snapping and layers on):
the selected-cell count oscillated between 30 and 40 per iteration for more than
19 iterations. The shortcut test had given a more favourable picture than the real run.
The setting used here is the surface-refinement `resolveFeatureAngle`; errata E6
describes how this was later confused with the `includedAngle` of the feature
extraction.

**The 120° run with layers.** Castellation converged cleanly (about 6.2 million cells)
and the layer table reported 18 of 18 layers with the intended thickness. The machine
then crashed at "Setting up information for layer truncation", twice at the same point.
The WSL2 memory ceiling was 12 GB on a machine with 15.85 GB of RAM, and raising it
further risked the Windows host. A half-domain version of the same set-up (symmetry plane
at y = 0, about 3.1 million cells before layers) crashed as well. Since halving the cells
did not avoid the crash, a simple "not enough memory for this many cells" explanation
was weakened, and the layer-displacement calculation at the sharp rear corners became a
suspect. A test that coarsened the surface level to (2 3) to isolate it ended with zero
layers, which reproduced the original thickness mismatch, so it did not answer the
question. The original README also states that the layer failure was reproduced on a mesh
6,300 times smaller than the full-resolution attempt; that test is not described in the
original mesh notes, so it is reported here without detail.

**Half-domain argument.** The half-domain was justified in the original notes by
the bistable rear wake of the Ahmed body, cited to Krajnovic (2014). That citation is
likewise unchecked. The argument itself holds up without it: a steady solver cannot
represent time-dependent switching of the wake, so imposing symmetry removes no physics
that a steady baseline could capture. It would not hold for an unsteady extension,
which would need the full domain.

## 3. The wall-function mesh

Layer extrusion was dropped. The wall treatment became `nutkWallFunction`,
`kqRWallFunction` and `omegaWallFunction` with surface refinement level (6 7),
`resolveFeatureAngle` 120 and the half-domain.

- 2,725,204 cells, no crashes.
- `checkMesh`: maximum non-orthogonality 32.9°, maximum skewness 0.95, maximum aspect
  ratio 3.42, no illegal faces.
- An analytic estimate put the wall-adjacent cells at y⁺ ≈ 97–194 at 60 m/s. The
  validation case later measured y⁺ on the same mesh level (see
  [transient-sweep.md](transient-sweep.md)) and found lower values.

## 4. Steady run

SIMPLEC, k–ω SST, `residualControl` 10⁻⁴, 2000 iterations. Residuals fell by about an
order of magnitude over the first 1000 iterations and then plateaued; only ω ever went
below 10⁻⁴.

Over iterations 1000–2000, Cd had mean 0.152808 and standard deviation 0.001670. The
mean of the last 100 iterations and of the last 200 differed by 0.027 %. A spectrum
showed a dominant period of 17.26 iterations (a peak 167,354 times the background), and
peak detection in the time domain gave 17.32 ± 0.46. Because the iteration counter of a
steady solver is a pseudo-time, the period has no physical frequency. It shows that the
solver settled into a limit cycle.

The relaxation factors (U 0.9, k and ω 0.5, inherited from a tutorial) were compared with
a bluff-body reference case (0.7) and left unchanged.

## 5. Moving to a transient run

A copy of the case was converted to PIMPLE. Two problems appeared.

1. **Steady versus transient is chosen by `ddtSchemes`.** The solver kept running in
   steady mode and exited at once, although the PIMPLE controls and time-step settings
   were correct. In OpenFOAM 11 the mode follows `ddtSchemes` in `fvSchemes`
   (checked in the source), and it had to be changed from `steadyState` to `Euler`.
2. **The steady flux field cannot restart a transient run.** Resuming from the SIMPLEC
   solution gave a mean Courant number of 1037 and a maximum of 107,343. Starting from
   uniform fields gave 0.0047 and 0.495. The run therefore starts from uniform
   initial conditions.

## 6. Cost and the coarser mesh

On the 2.7 million-cell mesh a time step took about 9–13 s, which meant 9–15 days for the
planned 0.435 s of flow time. Eight-way MPI decomposition helped. A first speed estimate
was wrong because it compared samples from different runs, and it was corrected with
consecutive samples from one run. Raising `maxCo` to 1 gave only about 20–30 % larger
steps, strained the pressure solver and one run died without a message, so `maxCo` stayed
at 0.5. Larger fixed time steps were rejected without a test, because the smallest cell
(0.96 mm) at about 100 m/s fixes the stable step.

The transient copy of the mesh was therefore coarsened in two steps (the steady mesh was
left alone):

| Surface level | Cells | Body surface faces | `checkMesh` |
|---|---|---|---|
| (6 7) | 2,725,204 | 452,339 | OK |
| (5 6) | 1,264,455 | 113,729 | OK (non-orthogonality 33.7°, skewness 1.06) |
| (4 5) | 872,391 | 28,369 | OK (non-orthogonality 29.7°, skewness 0.91) |

The loss of surface resolution is large and no mesh-independence study was made at the
coarser level. Two operational problems came up: `snappyHexMesh -overwrite` wrote the new
mesh into a numbered time directory instead of `constant/polyMesh`, and stale time
directories with old field sizes broke `decomposePar`. Both were fixed by hand.

## 7. First transient results

Cd started from a very large artefact (647 at t ≈ 0) and settled to about 0.162 by
t = 0.11 s (about 6.3 flow-through times), with no oscillation visible up to that point.
The run was then extended to t = 0.20 s.

- **Stationarity.** Windowed means of Cd (0.02 s windows) agreed within about 1–2 % from
  t = 0.045 s on, so t = 0.06–0.20 s was taken as the analysis window.
- **Frequency.** A first spectrum of the raw, unevenly sampled signal gave a "dominant
  period" about as long as the window, an artefact of the decaying start. After
  resampling to a uniform grid, the spectrum gave about 64–71 Hz depending on the window
  (coarse resolution of ±7–14 Hz). Peak-to-peak periods in two sub-windows were 0.01523 s
  and 0.01538 s (about 65.4 Hz). Cd and Cl gave the same frequency.
- **Probe check.** A velocity probe in the near wake gave 63.83 Hz by spectrum and 65.57 Hz
  by peak spacing, 0.33 % from the force-based value. Both come from the same run, so
  this shows that the signals are consistent. It does not show that the oscillation is
  physical.
- **Visualisation.** Seven frames of Ux on a y = 0.10 m slice show the recirculation
  region growing and shrinking over about two cycles.

The old notes do not explain why no oscillation was visible at t = 0.11 s and a clear one
was found in the window starting at 0.06 s.

## 8. What was corrected afterwards

| Statement in the original notes | Status |
|---|---|
| Strouhal number from body height (0.31–0.34) is "in line with verified literature" (Thacker et al. 2010: 0.18–0.21 and 0.24) | **Withdrawn** (E5): the cited values could not be found in the source. The height-based number f·H/U∞ ≈ 0.31 is arithmetic and a choice of length scale, not a validated match. |
| Bubble-pumping identified from the frames | Unsupported: it rested on the same literature. The frames show a changing recirculation region and nothing more. |
| The 65 Hz oscillation is a "confidently physical wake mode"; no steady solution exists | **Overstated** (E7): the evidence is internal consistency within one run on a coarse mesh. |
| The mesh is "validated" and the frequency "cross-validated" | Means internal consistency only. |
| Reported Cd, Cl | Half-body (E1); inlet turbulence about 5 % (E4). |
| Citations to Thacker 2012, Keogh, Krajnovic 2014 | Not verified. They support no conclusion here. |

The lessons that carry over to later work: a shortcut diagnostic (castellation-only) is
not evidence that the full configuration works; a failed layer calculation can come from
hardware limits as well as from meshing logic; and a statement about the literature needs
the paper in hand before it goes into a conclusion.
