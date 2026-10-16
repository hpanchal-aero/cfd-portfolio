# Corrections and Known Issues

This page records corrections to results and statements that appeared earlier in
Project 01, including earlier versions of the project README. The other documents
state the corrected position directly; this page explains what changed, why, and
what is and is not affected. The earlier README is preserved in git history:

```bash
git show pre-docs-rewrite:01-ahmed-body/README.md
```

Last updated 2026-10-15.

## Summary

| ID | What was wrong | Affects | Where it is handled |
|---|---|---|---|
| E1 | Every reported Cd, Cl and Cm is a half-body value (multiply by 2) | the 0°–35° sweep, including the frozen 25° case | [transient-sweep.md](transient-sweep.md) |
| E2 | The body rests on the floor at 0°, 10°, 20°, 30° and 35°; only 25° has the 50 mm clearance | the sweep | [transient-sweep.md](transient-sweep.md) |
| E4 | Inlet turbulence of the sweep is about 5 % (assumed), far above the experiments | all twelve sweep case directories | validation cases use matched turbulence |
| E5 | The Strouhal-number literature check is not supported | the 25° transient analysis, the mesh log | [transient-sweep.md](transient-sweep.md), [development-log.md](development-log.md) |
| E6 | `resolveFeatureAngle` and `includedAngle` were treated as one setting; the sweep meshes differ in curvature refinement | mesh comparability across angles | [transient-sweep.md](transient-sweep.md) |
| E7 | "A steady solution does not exist" and "the oscillation is physically real" are stronger than the evidence | the 25° sweep conclusions | [transient-sweep.md](transient-sweep.md) |

E3 (status of the frozen 25° case) is retired: its content is now part of the entries
above. The frozen 25° case has the E1 and E4 issues but, unlike the other angles, has
the 50 mm ground clearance; it remains unmodified.

**How to read the word "validated" in older material.** Where earlier text calls a
mesh "validated" or a wake frequency "cross-validated", it means internal consistency
(mesh quality checks; agreement between two signals taken from the same run). It does
not mean agreement with experiment. The only comparison with experimental data in this
project is in [validation-25deg.md](validation-25deg.md) and
[validation-35deg.md](validation-35deg.md).

---

## E1. All reported Cd, Cl and Cm are half-body values

**What was wrong.** The domain is a half-domain with a symmetry plane at y = 0, so the
`ahmedBody` patch is the half body. The `forceCoeffs` definition integrates the force
over that patch but normalises it with Aref = 0.112032 m², the **full** frontal area
(0.389 × 0.288 m), and applies no symmetry factor.

**Evidence.** On the 35° sweep mesh the patch spans y = 0 to 0.1945 m and its projected
frontal area is 0.056018 m², i.e. 0.5000 × 0.112032 (faces looking upstream and
downstream give the same area, so the patch is a closed surface). The same area was
later measured on the frozen 25° mesh (0.056019 m²) and on the two validation meshes
(0.056019–0.056020 m² at 25° and 0.056018 m² at 35°). All twelve sweep case directories
(steady and transient, 0°–35°) use the same `forceCoeffs` definition and the same
half-domain setup, so the same factor is expected everywhere, but the area was measured
on the meshes listed above only.

**Effect.** Assuming a symmetric mean flow, every reported Cd, Cl and Cm is half the
full-body value; the correction is a factor of 2.

| Case and window | Reported (half-body) | Multiplied by 2 |
|---|---|---|
| 0° steady, Cd, iterations 1200–2000 | 0.151413 | 0.302826 |
| 25° steady, Cd, iterations 1000–2000 | 0.152808 (std 0.001670) | 0.305616 (std 0.003340) |
| 10° transient, Cd | 0.1433 (std 0.0044) | 0.2866 (std 0.0088) |
| 10° transient, Cl | 0.5986 (std 0.0032) | 1.1972 (std 0.0064) |
| 20° | no mean Cd or Cl reported | — |
| 30° transient (0.06–0.2 s), Cd | 0.1629 (std 0.0057) | 0.3258 (std 0.0114) |
| 30° transient (0.06–0.2 s), Cl | 0.7615 (std 0.0067) | 1.5230 (std 0.0134) |
| 35° transient (0.14–0.30 s), Cd | 0.15890 (std 0.00300) | 0.31780 (std 0.00600) |
| 35° transient (0.14–0.30 s), Cl | 0.71462 (std 0.00255) | 1.42924 (std 0.00510) |

Other Cd, Cl and Cm values quoted for the sweep (window-sensitivity values, sub-window
means) scale by the same factor.

**Not affected:** flow fields, pressure and velocity statistics, frequencies and
Strouhal-number analyses, mesh quality, percentage-type statistics (sub-window spreads,
drift/std ratios) and the qualitative conclusions about wake behaviour.

**Validation cases.** The corrected cases (`val25_clr50_*`, `val35_clr50_*`) set
Aref = 0.056016 m², half of the full frontal area, so their coefficients are full-body
coefficients.

## E2. The body sits on the ground plane in the 0°, 10°, 20°, 30° and 35° cases; the 25° case has the 50 mm clearance

*An earlier version of this item (commit `612e1dd`) said the clearance was missing in
every case including 25°. That was wrong. It had been inferred from the generator's STL
files and from a measurement on the 35° mesh, before the 25° case's own STL had been
opened. It was corrected on 2026-10-04.*

**What was wrong.** The reference configuration includes a 50 mm ground clearance. The
geometry generator builds the body with its underside at z = 0 and leaves the clearance
to the case setup. The STL used inside each case directory shows what was simulated:

- the three 25° case directories use an STL raised by 50 mm (z = 0.050 to 0.338 m);
- the STLs in all other case directories (0°, 10°, 20°, 30°, 35°) span z = 0 to 0.288 m,
  i.e. the body rests on the floor (domain floor at z = 0, identical `blockMeshDict` in
  these cases; the early `slant25_re4.29M` directory has a different `blockMeshDict` and
  was examined through its STL only).

**Checked on the meshes.**

- 25° (frozen mesh): `ground` patch at z = 0; body patch z = 0.050 to 0.338 m; projected
  area in z of 0.20091 m² facing up and 0.20091 m² facing down, so the underside face is
  present and there is an underbody gap.
- 35° (sweep mesh): `ground` patch at z = 0; body patch z = 0 to 0.288 m; downward-facing
  projected area 0.0152 m² against 0.2009 m² facing upward, so there is no underside face
  and no underbody gap.
- 0°, 10°, 20°, 30°: the conclusion rests on the STL files and the common domain
  definition; their meshes were not measured.

**Consequences.**

- The sweep is internally inconsistent: the 25° case includes an underbody gap and its
  flow, the other angles do not. Trends of Cd and Cl across slant angle (even after the
  factor 2 of E1) mix two geometries and must not be read as a slant-angle effect.
- For the five angles without clearance the simulated geometry is a body resting on the
  ground plane, with no underbody flow. Their absolute coefficients, and lift in
  particular (the doubled 35° Cl of about 1.4 is not a result), are not comparable with
  published Ahmed-body data.
- Observations about wake dynamics describe the geometry that was actually simulated at
  each angle.

## E4. Inlet turbulence differs strongly from the reference experiments

**What was wrong.** All twelve sweep case directories (steady and transient, 0°–35°) use
one identical `0/include/initialConditions` file (verified by checksum): U = 60 m/s,
k = 13.5 m²/s², ω = 91.79 1/s. The file records the turbulence intensity as **assumed** to
be 5 % (k = 1.5 (U·I)², ω from a length scale of 0.07 L). With ν = 1.5×10⁻⁵ m²/s this
gives a free-stream eddy-viscosity ratio νt/ν = k/(ω ν) of about 9.8×10³. The earlier
README did not state these values.

**Reference values.** According to the ERCOFTAC AC1-05 documentation, the reference
experiments report a turbulence intensity below 0.5 % (Ahmed et al. 1984, 60 m/s) and
below 0.25 % with a viscosity ratio of about 10 (Lienhart et al., 40 m/s). At the inlet,
the sweep's intensity is therefore 10 to 20 times higher and its viscosity ratio about
980 times higher. Turbulence decays along the 2.088 m inlet length; an analytic estimate
with the SST decay constants (β = 0.0828, β* = 0.09) still gives about 4.4 % and
νt/ν ≈ 9,600 at the nose. That is an estimate, not a simulation result, and the decay
was not measured in the sweep cases.

**Effect.** Not tested. A high free-stream eddy viscosity could damp unsteadiness and
smear shear layers, which would bear on the wake-dynamics observations, but that is a
hypothesis, not a finding. The unsteady results of the sweep are results for this inlet
condition. The validation cases use inlet turbulence matched to the experiments (nose
Tu 0.25 %, νt/ν = 10).

## E5. The Strouhal-number literature check is not supported

The earlier 25° transient analysis stated that the characteristic length of the Strouhal
number (body height H) was "verified against literature, not assumed", cited "Thacker et
al. 2010, on this same 25° geometry", and compared the result with a published range of
0.18–0.21 and with "0.24 (aspect-ratio studies)". The mesh log repeats these statements.
On 2026-10-11 they were checked and are **not supported**:

- The 25° rear-slant study by Thacker, Aubrun, Leroy and Devinant (Experiments in Fluids
  54, 1479, 2013; DOI 10.1007/s00348-013-1479-5) defines its Strouhal numbers on the mean
  reattachment length (about 0.11 for the 20 Hz bubble and shear-layer motion, 0.6–0.7 for
  high-frequency shear-layer activity) and, for Kelvin–Helmholtz vortices, on the
  shear-layer vorticity thickness (about 0.2). It reports no 0.18–0.21 slant-surface
  shedding Strouhal number defined on body height, and its reference list contains no
  Thacker 2010 paper (its only Thacker reference is J. Wind Eng. Ind. Aerodyn. 107–108,
  237–243, 2012). No source was found for the "2010" citation, for 0.18–0.21 as defined
  there, or for 0.24. They are unverified and are withdrawn as comparison values.
- St = f·H/U∞ with H = 0.288 m is a **choice of definition**, not a literature-verified
  convention. The frequency (about 65.4 Hz) is unchanged. The arithmetic is consistent
  (the body-length value 1.14 and the height-based value 0.31 differ by L/H = 3.625), but
  the statement that literature supports the height-based convention is unsupported. The
  statement that St 0.31–0.34 is "on the higher end of published values" is withdrawn: no
  valid published comparison value is given anywhere in this project.
- "Cross-validated" refers to the 0.33 % agreement between the force frequency and a
  wake-probe frequency, both taken from the same transient run. That shows the oscillation
  is a consistent feature of this simulation. It is **not** validation against experiment
  and does not show that the oscillation is physical; the inlet turbulence of E4 and the
  coarsened transient mesh remain untested influences.

## E6. `resolveFeatureAngle` and `includedAngle` are different settings; the sweep meshes differ in curvature refinement

**What was wrong.** The 0° and 25° feature-angle work swept the `surfaceFeatures`
utility over `includedAngle` and then used the same number for `resolveFeatureAngle` in
`snappyHexMeshDict`, on the assumption that both describe the same edge selection. They
do not, and the mesh reads only one of them.

- Every case's `snappyHexMeshDict` has an empty explicit-feature list (`features ( );`),
  and every `snappyHexMesh` log reports `distance to explicit features : 0 cells`. The
  `.eMesh` file produced by `surfaceFeatures` was never read by any mesh in this project.
  The edge analysis built on it (for example 0°'s eight edges) is a valid geometric
  characterisation of the STL, but it never drove any refinement.
- The setting that acts on the mesh is `resolveFeatureAngle`. From the OpenFOAM 11 source
  (`refinementParameters.C`) it is converted to `curvature = cos(resolveFeatureAngle)`,
  and a cell is marked for curvature refinement where two neighbouring surface-triangle
  normals satisfy `dot(n_i, n_j) < curvature`, that is, where adjacent normals differ by
  **more** than `resolveFeatureAngle`. This is not the same quantity as `includedAngle`
  (`180° − includedAngle` for the convention verified in this project).

**Effect on the sweep meshes.**

| Angle | `resolveFeatureAngle` | Curvature-marked cells in the steady mesh |
|---|---|---|
| 0° | 90 | 3,229 |
| 10° | 90 | 2,607 |
| 20° | 70 | 3,103 |
| 25°, 30°, 35° | 120 | 0 (cannot fire: no edge on this body exceeds a 90° normal difference) |

The 0°, 10° and 20° meshes therefore received curvature-based edge refinement and the
25°, 30° and 35° meshes did not, an unintended cross-angle difference. At 10°, the
slant-to-rear edge and the roof-to-slant crease were also not selected at
`includedAngle 90`; the dictionary comments calling them captured and verified were
wrong and were corrected in the case files.

**Related caveats.**

- The 20° mesh log reports 3,103 marked cells, but their spatial location (whether they
  sit at the intended slant-to-rear edge) was not inspected.
- At 35° the first `includedAngle` detector counted points that were in fact the top ends
  of the vertical rear-face edges and reported the slant-to-rear edge at every angle from
  115° to 130°. It was replaced with a connectivity-based detector, which places the edge
  between 124° and 125°. The 10°, 20° and 30° sweeps were done earlier and were **not**
  re-verified with the corrected detector.

## E7. "A steady solution does not exist" and "the oscillation is physically real" are stronger than the evidence

*Added in the documentation rewrite of 2026-10-15. This item was not part of the earlier
README, which stated both conclusions without qualification.*

**What was stated.** The earlier conclusions said that no steady RANS solution exists for
the 25° flow, and that the 65 Hz wake oscillation is physically real and not a numerical
artifact, supported by three independent lines of evidence.

**What the evidence shows.**

- *Steady solver.* In the steady SIMPLEC run the residuals plateaued after iteration 1000
  and Cd oscillated with a period of 17.26 iterations (mean 0.152808 half-body, std
  0.001670; spectral peak 167,354× the background). Iteration count is a pseudo-time
  relaxation parameter, so this period has no physical frequency. That the solver does not
  converge to a fixed point with these settings is an observation. That it signals real
  flow unsteadiness is an interpretation. The k and ω relaxation factors (0.5) are more
  conservative than the 0.7 of a bluff-body reference case; they were inspected and never
  varied, so a contribution from solver settings is untested. The corrected validation
  cases show the same behaviour (final U_z residual of order 2×10⁻², Cl std of about 0.07
  in all three cases) and were nevertheless used as stationary means.
- *Transient oscillation.* The oscillation (about 65 Hz) was found in the force signals
  and in a wake probe of one transient run on a mesh coarsened about 3.1× from the steady
  mesh, with the assumed 5 % inlet turbulence of E4. The two signals agree within 0.33 %,
  but they come from the same run, so their agreement shows internal consistency only (E5).
  No experimental frequency was available for comparison.

**Corrected statement.** The 25° steady solver at these settings does not converge to a
fixed point and the transient run shows a persistent wake oscillation near 65 Hz. Whether
the flow is intrinsically unsteady, and whether the oscillation is physical and not an
effect of the inlet turbulence, the coarsened mesh or the solver settings, is **not
established**.
