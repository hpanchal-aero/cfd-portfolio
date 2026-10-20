# Fixed cylinder, Re = 100: domain-size study

Working note, written 2026-10-20. Medium mesh, dt = 0.0025, 2D laminar
incompressible, same settings as the baseline in note 03. Nothing here is
validation; all of it is verification (numerical uncertainty of the domain size).

## Set-up

Baseline domain: x = -15 ... 30, y = +/-15, thickness 0.1 (cylinder D = 1 at the
origin). Blockage D/H = 1/30 = 3.3 % at baseline.
Each case changes one boundary only; all other settings are identical to the
baseline (the `system/`, `constant/` and `0/` files were compared with `diff`
and are identical, `constant/polyMesh` excluded).

| case | change | cells | total volume | mesh md5 (8 chars) |
|---|---|---|---|---|
| base | none (x -15..30, y +/-15) | 28,663 | 134.921 | be32ad72 |
| regen | baseline regenerated (replicate) | 28,663 | 134.921 | 914d2962 |
| y30 | y = +/-30 | 29,474 | 269.921 | 89bb412d |
| xin30 | x_in = 30 | 28,884 | 179.921 | 70dfabc1 |
| xout60 | x_out = 60 | 29,065 | 224.921 | 70c9e859 |
| xin60 | x_in = 60 | 29,417 | 269.921 | d3ec750c |

Mesh quality (checkMesh): xin30 max skewness 1.283 (two faces above 1.0 on the
wake-box edge, at (8.20, -2.71) and (13.97, 2.27)), max non-orthogonality
36.52, max aspect ratio 16.28. xin60 max skewness 0.812, max non-orthogonality
39.50 (average 5.79), max aspect ratio 15.89. All meshes pass checkMesh.
Regenerating the baseline gives the same cell count and near-identical quality
but a different file (hence the md5 per case in `mesh.md5`).

An extra mesh, xin30b (xin30 generated again), was made for the diagnostic below
and not run: 28,884 cells, skewness 1.28263 and non-orthogonality 36.5239 as
xin30, aspect ratio 16.2655 against 16.2757, md5 e68cd67d. Not committed.

## Rules fixed before the results

- D7b (2026-10-19, before any domain result): the domain-size term of the
  validation rule is the SUM of the absolute changes of the three single-boundary
  runs (y30, xin30, xout60) per quantity, each relative to the enlarged-domain
  value. Replicate scatter is reported as the resolution limit: a change below it
  is flagged "not resolved" but still counted at its measured value. The
  replicate is not an extra term and is not subtracted. Floors unchanged.
- xin30 diagnostic (2026-10-19, before the domain results were read): if the xin30
  change exceeds the replicate scatter, generate xin30 again and check that the
  change does not depend on that mesh realisation. Outcome: the regenerated xin30
  mesh is practically identical (cells, skewness, non-orthogonality, volume), so a
  run would repeat the first one. Not run. This rules out random scatter between
  mesh realisations; it does not rule out a mesh-topology effect of xin30
  relative to the baseline, which is why xin60 was added.
- D7c (2026-10-19, before the xin60 run had finished): the upstream effect is
  "converging" if, for a quantity, |30 -> 60 change| < 0.5 x |15 -> 30 change|;
  otherwise "not converging / unexplained". No new term enters the validation
  rule from this run.

## Run integrity

- All five runs reached t = 200 and 80,001 force rows (the baseline's count). The
  only hit of the warning/fatal/floating-point/nan pattern is the sigFpe header
  line. The logs end with `End`.
- In-run Courant maximum for t >= 100: 0.29-0.33 for y30, xin30, xout60, regen;
  0.324 for xin60. The larger values printed before the first step (1.17-1.21,
  all five runs) are initial-field values; for xin60 the first computed step is
  0.364.
- All runs are periodic at the analysis window (xin60: per-cycle Cd constant at
  1.34673 from t about 117, period 6.0097 with std 2e-5).
- Analysis: nine whole shedding periods inside t = 120-180 (windows start between
  t = 122.9 and 124.1), Strouhal number from zero crossings (FFT agrees: xin60
  0.16640 both).

## Results

Table A: the D7b domain-size term (% of the enlarged-domain value)

| quantity | base | y30 | xin30 | xout60 | regen | dy30 % | dxin % | dxout % | sum % | replicate % |
|---|---|---|---|---|---|---|---|---|---|---|
| St | 0.16717 | 0.16648 | 0.16634 | 0.16722 | 0.16718 | 0.417 | 0.505 | 0.028 | 0.950 | 0.000 |
| Cd mean | 1.35650 | 1.35059 | 1.34856 | 1.35734 | 1.35647 | 0.437 | 0.589 | 0.062 | 1.088 | 0.002 |
| Cl rms | 0.22952 | 0.22842 | 0.22664 | 0.22982 | 0.22951 | 0.483 | 1.272 | 0.128 | 1.883 | 0.005 |
| Cl amplitude | 0.32478 | 0.32322 | 0.32065 | 0.32506 | 0.32477 | 0.482 | 1.287 | 0.085 | 1.855 | 0.004 |

No change is below the replicate scatter ("not resolved": none).

Table B: upstream convergence (signed, (smaller - larger domain value) / larger
domain value, %)

| quantity | xin30 | xin60 | 15 -> 30 | 30 -> 60 | ratio | rule | 15 -> 60 | D7b xin30 term |
|---|---|---|---|---|---|---|---|---|
| St | 0.16634 | 0.16640 | 0.505 | -0.037 | 0.07 | converging | 0.467 | 0.505 |
| Cd mean | 1.34856 | 1.34673 | 0.589 | 0.136 | 0.23 | converging | 0.725 | 0.589 |
| Cl rms | 0.22664 | 0.22558 | 1.272 | 0.470 | 0.37 | converging | 1.747 | 1.272 |
| Cl amplitude | 0.32065 | 0.31911 | 1.287 | 0.485 | 0.38 | converging | 1.778 | 1.287 |

Both tables: `scripts/analysis/domain_table.py` from the window results in
`results/exploratory/`.

## Findings

1. Every domain change is far above the replicate scatter (<= 0.005 %); the
   changes are real properties of the domain, not noise.
2. Downstream extent (x_out 30 -> 60) does not matter: <= 0.13 %.
3. Cross-flow extent (blockage 3.3 % -> 1.7 %) changes St, Cd and Cl by 0.4-0.5 %,
   all downward. The sign is what reduced blockage would give; I have not
   checked this against a source.
4. Upstream extent has the largest effect in every quantity (0.5 % in St and Cd,
   1.3 % in Cl), which I did not expect: I had named the cross-flow extent as the
   likely dominant term. xin60 shows the effect converging by the rule above.
   The xin60 mesh has no skewed faces and still agrees with xin30, which argues
   against a mesh artefact in xin30; two meshes of the same recipe do not
   establish that completely. No physical explanation of why the inlet distance
   matters this much has been tested.
5. D7b is applied unchanged. Domain-size term (sum): St 0.95 %, Cd 1.09 %, Cl rms
   1.88 %, Cl amplitude 1.86 %. Together with the other terms measured so far (as
   % of the finer value): St 0.07 (mesh) + 0.02 (time step) + 0.95 (domain);
   Cd 0.09 + 0.07 + 1.09; Cl rms about 1.6 + 0.63 + 1.88. The domain is the
   dominant numerical term for St and Cd. All sums are below the floors
   (St 2 %, Cd 3 %, Cl rms 10 %), so the floors decide the bands unless a
   reference uncertainty turns out to be larger (nothing is known about that yet).

## Limitations

- The D7b term uses the xin30 change for the upstream part, which understates
  the upstream effect relative to xin60 by 0.14 % (Cd), 0.47 % (Cl rms) and
  0.49 % (Cl amplitude); for St the xin60 total is smaller than the xin30 term.
- Single runs per domain; replicate only at the baseline domain.
- The sum assumes the three effects are additive; no run changes two
  boundaries at once, and xin60 was run with the baseline cross-flow extent.
- No extrapolation to an infinite domain; two steps do not give a rate.
- One Reynolds number (100); Re = 150 domain effects are not measured.
- Mesh and time-step errors for Cl are larger than for St and Cd (note 03), and
  the mesh x time-step interaction is untested.
- Raw force histories are in `postProcessing/`, which is not tracked.

## Open decision

Which domain the production runs (Re = 150 fixed cylinder and the coupled
cases) should use: the baseline or an enlarged one. Not decided; to be brought
to the user with the cost of each option.

## Reproduction

Meshes: `MESH_TAG=<tag> MESH_ARGS="<args>" scripts/meshing/mesh_case.sh medium <case_dir>`
with args `--y-half 30`, `--x-in 30`, `--x-out 60`, `--x-in 60`, none for regen.
Set-up: `scripts/run/setup_fixed.sh <case_dir> 100 0.0025 200`. Run: `foamRun` in
the case directory. Analysis: `scripts/analysis/force_signal.py <forceCoeffs.dat>
--t0 120 --t1 180 --json <file>` then `scripts/analysis/domain_table.py`.
