# Fixed cylinder: numerical verification (Re = 100 and Re = 150)

This document estimates the numerical uncertainty of the fixed-cylinder results: the Strouhal number St, the
mean drag coefficient C_D and the lift coefficient (rms and amplitude). It asks whether the equations were
solved accurately enough, not whether the model agrees with experiment; the comparison with reference data is in the README of this project (section Comparison with reference data). The set-up is described in method.md.

## 1. Cases and statistics

All cases are two-dimensional and laminar, with the numerics of method.md (time step 0.0025 unless stated).
Re = 100 uses nu = 0.01, Re = 150 uses nu = 1/150. The baseline domain is x from -15 to 30 D, |y| < 15 D.

| Study | Cases |
|---|---|
| Mesh | coarse, medium, fine (14,440 / 28,663 / 54,558 cells) at Re = 100; medium and fine at Re = 150 |
| Time step | dt = 0.005, 0.0025, 0.00125 on the medium mesh at Re = 100; 0.0025 and 0.00125 at Re = 150 |
| Domain (one boundary changed per run) | cross-flow half-height 30 D (y30), inlet at 30 D (xin30), outlet at 60 D (xout60); Re = 100 also inlet at 60 D (xin60) |
| Domain (combined) | Re = 150: 30 / 60 / 30 D (dom-big, 31,288 cells) and 45 / 90 / 45 D (dom-big2, 36,358 cells), given as inlet / outlet / half-height |
| Replicate | baseline mesh regenerated with a new Gmsh run (same settings) at both Reynolds numbers |

The Re = 150 meshes are copied unchanged from the Re = 100 cases; only the viscosity changes. The domain-study
meshes were generated separately for each domain; their cell counts are 28,663 (baseline), 29,474 (y30),
28,884 (xin30), 29,065 (xout60), 29,417 (xin60). All pass checkMesh. The worst case is xin30, with a maximum
skewness of 1.283 (two faces above 1.0 on the edge of the wake refinement box).

Statistics are taken over whole shedding periods inside t = 120 to 180 (first to last upward zero crossing of
C_L; 9 periods at Re = 100, 10 at Re = 150). St comes from the zero crossings and agrees with an FFT to four
digits. The C_L amplitude is (max - min)/2 over the window. The same window and estimator are used in every
row.

## 2. Are the runs periodic?

Every run reached t = 200 and its log ends normally; the only match of a scan for nan, fatal errors and
floating-point exceptions is the header line that announces exception trapping. At Re = 150 the reference
run is periodic from t of about 90 (C_L amplitude 0.5110 and period 5.3755 constant from t of about 80 to
200). The mesh and domain runs are constant over all cycles from t = 100.

The runs with a halved time step were restarted at t = 100 from the saved state of the reference run. After
the restart the flow relaxes onto the limit cycle of the new step, each cycle deviating by about 0.4 of the
previous one. At Re = 150 the C_L amplitude settles through 0.5098, 0.5085, 0.5080, 0.5079, 0.5078, 0.5077;
at Re = 100 through 0.3236, 0.3232, 0.3230, 0.3229, 0.3228. The analysis window contains at most one cycle
that is 0.0001 off in C_L amplitude. The effect on the window mean is about 0.003 %, against a time-step term
of 0.6 %. The criterion (the cycles inside the window agree to the last printed digit) was fixed before the
cycles were read.

Maximum Courant number for t >= 100, Re = 150: 0.273 (medium), 0.378 (fine), 0.136 (medium, half the step).

## 3. Mesh

Re = 100 (dt = 0.0025 on all three meshes):

| Mesh | St | Mean C_D | C_L rms | C_L amplitude |
|---|---|---|---|---|
| coarse | 0.16656 | 1.35610 | 0.22443 | 0.31767 |
| medium | 0.16717 | 1.35650 | 0.22952 | 0.32478 |
| fine | 0.16729 | 1.35774 | 0.23334 | 0.33007 |

The medium to fine change, as a percentage of the fine value, is St 0.070 %, mean C_D 0.092 %, C_L rms
1.635 % and C_L amplitude 1.604 %. The increments of mean C_D grow with refinement (ratio of successive
changes 0.32), so no error is extrapolated for it. For C_L the observed rate of convergence is about 0.9
(ratio 1.34); if it continued, the fine mesh would still be about 4 to 5 % below the mesh-independent value
and the medium mesh about 6 %. This is an extrapolation from three points and is only an estimate. The
change of St is not an order of convergence (ratio 5.2).

Re = 150 (medium to fine, in % of the fine value): St 0.109, mean C_D 0.303, C_L rms 2.207, C_L amplitude
2.191. The mesh term is larger than at Re = 100 (by factors of 1.6 for St, 3.3 for mean C_D and 1.35 for C_L
rms), in the direction expected from the thinner boundary layer (its thickness scales as Re^-1/2, about 18 %
thinner). C_L is mesh-dominated at Re = 150. There is no coarse mesh at Re = 150, so no convergence order or
extrapolated error can be given there.

## 4. Time step

Re = 100, medium mesh:

| dt | St | Mean C_D | C_L rms | C_L amplitude | Period |
|---|---|---|---|---|---|
| 0.005 | 0.16711 | 1.35798 | 0.23175 | 0.32794 | 5.98407 |
| 0.0025 | 0.16717 | 1.35650 | 0.22952 | 0.32478 | 5.98177 |
| 0.00125 | 0.16721 | 1.35559 | 0.22808 | 0.32290 | 5.98066 |

The last halving changes St by 0.019 %, mean C_D by 0.067 %, C_L rms by 0.635 % and the C_L amplitude by
0.581 %. The observed order in time is 0.72 (mean C_D), 0.75 (C_L amplitude), 0.62 (C_L rms) and 1.05
(St and period). The scheme is nominally second order, and a second-order error was predicted before the
runs; the observation rejects it. The cause is not established. The working hypothesis is a first-order
splitting error of the pressure-velocity coupling (two correctors, one outer iteration); it is untested. At
Re = 150 only one halving exists: St 0.039 %, mean C_D 0.094 %, C_L rms 0.652 %, C_L amplitude 0.639 %.

Stability: with dt = 0.005 the coarse and medium meshes are stable, and the fine mesh diverged within the first
steps (and again when restarted from a smooth state at t = 5). dt = 0.0025 is stable on all three meshes. A
Courant limit near 0.6 to 0.7 is an inference from three runs, not a measurement. The mesh study therefore
uses dt = 0.0025 on every mesh. Whether the time-step error depends on the mesh is untested (the fine mesh was
run at dt = 0.0025 only).

## 5. Domain

Re = 100: change of each quantity when one boundary is moved, in % of the value in the larger domain.

| Quantity | Baseline | y30 | xin30 | xout60 | Replicate | y30 % | xin30 % | xout60 % | Sum % |
|---|---|---|---|---|---|---|---|---|---|
| St | 0.16717 | 0.16648 | 0.16634 | 0.16722 | 0.16718 | 0.417 | 0.505 | 0.028 | 0.950 |
| Mean C_D | 1.35650 | 1.35059 | 1.34856 | 1.35734 | 1.35647 | 0.437 | 0.589 | 0.062 | 1.088 |
| C_L rms | 0.22952 | 0.22842 | 0.22664 | 0.22982 | 0.22951 | 0.483 | 1.272 | 0.128 | 1.883 |
| C_L amplitude | 0.32478 | 0.32322 | 0.32065 | 0.32506 | 0.32477 | 0.482 | 1.287 | 0.085 | 1.855 |

The downstream extent hardly matters (0.13 % or less). The cross-flow extent (blockage 3.3 % to 1.7 %) changes
St, mean C_D and C_L by 0.4 to 0.5 %, all downward, which is the sign reduced blockage would be expected to
give (not checked against a source). The upstream extent has the largest effect in every quantity (0.5 % in
St and mean C_D, about 1.3 % in C_L), which was not expected. A run with the inlet at 60 D shows the effect
converging by a rule fixed before that run finished (the change from 30 to 60 D smaller than half the change
from 15 to 30 D):

| Quantity | 15 to 30 D % | 30 to 60 D % | Ratio | 15 to 60 D % |
|---|---|---|---|---|
| St | 0.505 | -0.037 | 0.07 | 0.467 |
| Mean C_D | 0.589 | 0.136 | 0.23 | 0.725 |
| C_L rms | 1.272 | 0.470 | 0.37 | 1.747 |
| C_L amplitude | 1.287 | 0.485 | 0.38 | 1.778 |

The xin60 mesh has no skewed faces and still agrees with xin30, which argues against a mesh artefact in
xin30. Two meshes of the same recipe do not rule it out completely. No physical explanation of why the inlet
distance matters this much has been tested. A fifth mesh (xin30 generated again) was prepared for a diagnostic
and not run: its cell count, skewness, non-orthogonality and volume are practically identical to xin30, so a
run would repeat the first one.

Re = 150: single-boundary changes in % of the larger-domain value, and the changes towards the combined
domains (baseline values: St 0.18603, mean C_D 1.33791, C_L rms 0.36103, C_L amplitude 0.51102):

| Quantity | y30 | xin30 | xout60 | Sum | Baseline to dom-big | Baseline to dom-big2 | dom-big to dom-big2 |
|---|---|---|---|---|---|---|---|
| St | 0.404 | 0.447 | 0.033 | 0.884 | 0.966 | 1.343 | 0.373 |
| Mean C_D | 0.373 | 0.565 | 0.120 | 1.058 | 1.516 | 1.983 | 0.460 |
| C_L rms | 0.252 | 0.852 | 0.287 | 1.391 | 2.474 | 2.610 | 0.133 |
| C_L amplitude | 0.252 | 0.833 | 0.264 | 1.349 | 2.490 | 2.631 | 0.138 |

At Re = 150 the three single-boundary effects do not add up. The measured change to dom-big is 1.84 times the
sum for mean C_D and 2.98 times for C_L rms (hand arithmetic); for St the sum underestimates the combined
change by about 0.1 percentage points. The domain term used for Re = 150 is therefore the measured change from
the baseline to the largest domain (dom-big2), not the sum. Re = 100 has no combined-domain run, so there the
domain term is the sum of the single-boundary changes, and that sum is the smaller of the two possible
estimates. The series has not converged for St and mean C_D at 45 / 90 / 45 D: the step from dom-big to
dom-big2 (0.373 % and 0.460 %) is as large as a single-boundary effect. C_L rms is nearly flat (0.133 %). The
ratio of the second step to the first is 0.39 for St and 0.30 for mean C_D, close to the 0.33 that scaling with
1/half-height would give; this is an observation from two points, and no extrapolation is used.

Possible origin of the non-additivity, untested: the number of mesh points within 2 D of the cylinder differs
by up to 1.6 % between the baseline, dom-big and dom-big2 meshes (8693, 8555 and 8713), while the boundary-layer
ring (r < 0.6 D) is identical (2928 points).

## 6. Replicate

A baseline mesh regenerated with a new Gmsh run (same cell count and nearly identical quality, different file)
gives the following differences, in % of the replicate value. Re = 100: St 0.000, mean C_D 0.002, C_L rms
0.005, C_L amplitude 0.004. Re = 150: 0.000, 0.002, 0.004, 0.003. This is the reproducibility for identical
input and the resolution limit of the other terms; every domain change above is much larger. It does not
contain the sensitivity to the near-body mesh topology, which changes when the domain extents change (see
above). An earlier expectation that the scatter would be near 1 % was wrong.

The Re = 150 replicate was interrupted by a machine crash at t = 165.08 and restarted from the last saved time
(160). Over the overlap the restarted run differs from the first by at most 9.1e-7 in C_D and 2.4e-6 in C_L,
both at the first step, where backward time stepping falls back to first order, and decaying afterwards.

## 7. Summary of the numerical terms

Mesh term: medium to fine. Time-step term: last halving on the medium mesh. Domain term: sum of the
single-boundary changes at Re = 100; baseline to dom-big2 at Re = 150. All in % of the finer or larger-domain
value; the sum is a simple sum of the three terms.

| Re | Quantity | Mesh | Time step | Domain | Sum |
|---|---|---|---|---|---|
| 100 | St | 0.070 | 0.019 | 0.950 | 1.04 |
| 100 | Mean C_D | 0.092 | 0.067 | 1.088 | 1.25 |
| 100 | C_L rms | 1.635 | 0.635 | 1.883 | 4.15 |
| 150 | St | 0.109 | 0.039 | 1.343 | 1.49 |
| 150 | Mean C_D | 0.303 | 0.094 | 1.983 | 2.38 |
| 150 | C_L rms | 2.207 | 0.652 | 2.610 | 5.47 |

The sums are small compared with the agreement floors set for the validation (St 2 %, mean C_D 3 %); how they enter the agreement bands is described in the README of this project (section Comparison with reference data). For C_L rms at Re = 150, the domain term (a
decrease) and the mesh term (an increase on the fine mesh) have opposite signs and partly cancel, so neither
should be quoted alone.

## 8. Limitations

- Re = 150 has no coarse mesh, no upstream-60 domain run, and one time-step halving only; the upstream
  convergence found at Re = 100 is not measured at Re = 150, so the single-boundary upstream term may
  understate the effect there.
- Re = 100 has no combined-domain run, so its domain term is probably the smaller estimate.
- The three single-boundary effects are summed, which assumes additivity; at Re = 150 the combined run shows
  that the assumption fails for the forces.
- The domain series is not converged for St and mean C_D, and no extrapolation to an infinite domain is made.
- The mesh levels were generated separately, and the near-wall resolution scales with the level, so the
  refinement is not a pure change of cell size. The interaction of mesh and time step is untested.
- The time-step order is slower than second order for reasons not established; one halving is not an error
  estimate.
- The C_L results are not mesh-converged at either Reynolds number.

## 9. Reproduction

The committed result files are the windowed analyses `results/exploratory/Re<Re>_<case>_w120-180.json`;
the tables above are printed by `scripts/analysis/verification_table.py <Re>` and
`scripts/analysis/domain_table.py`. The raw force histories, logs and time directories are not tracked, so
the numbers can be rebuilt from the committed result files but not from raw data without rerunning:

1. mesh: `MESH_TAG=<tag> MESH_ARGS="<args>" scripts/meshing/mesh_case.sh medium <case_dir>` (args
   `--y-half 30`, `--x-in 30`, `--x-out 60`, `--x-in 60`, none for the replicate);
2. case: `scripts/run/setup_fixed.sh <case_dir> <Re> 0.0025 200` or, for a derived case,
   `scripts/run/derive_case.sh <src_case> <dst_case> <Re> <deltaT> <endTime> [restart_time]`
   (the Re = 150 cases are derived from the Re = 100 cases; the half-step case restarts from t = 100);
3. run: `scripts/run/launch_case.sh <case>`; check and analyse:
   `scripts/analysis/check_run.sh <case> <json>`, which uses
   `scripts/analysis/force_signal.py <forceCoeffs.dat> --t0 120 --t1 180 --json <file>`.

The committed controlDict of the replicate at Re = 150 has startTime 160 (the restart); for a run from
scratch set startTime 0. The mesh of each case is identified by the checksum in `mesh.md5`, because Gmsh does
not return identical files between runs.
