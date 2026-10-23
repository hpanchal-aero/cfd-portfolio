# Note 07 -- moving-mesh feasibility (D3), Re = 150

Date: 2026-10-22 / 23.  Working note, to be rewritten into the final docs.

## Purpose
D3 chose OpenFOAM's sixDoFRigidBodyMotion with PIMPLE outer iterations, with feasibility in OpenFOAM 11
under foamRun still to be tested. This note records that test: can a spring-mounted cylinder move with the
mesh, with the forces coupled correctly and the coupling stable?

## Set-up (read from the OpenFOAM 11 source, not assumed)
- Solver: foamRun, incompressibleFluid, laminar, Re = 150, same mesh and dt = 0.0025 as the fixed-cylinder
  reference (fixed_Re150_medium_dt0.0025).
- Mover (constant/dynamicMeshDict, entry "mover"): sixDoFRigidBodyMotion on patch "cylinder".
  - constraints: plane (normal (0 0 1)) and orientation (rotation locked): motion in x-y only.
  - restraint: linearSpring, force = -k (|r| - L0) r_hat - c (r_hat . v) r_hat, anchor = attachment point =
    (0 0 0), restLength 0, damping 0 (zeta = 0, D2). With L0 = 0 this is an isotropic 2-D spring.
  - innerDistance / outerDistance are measured from the cylinder wall; the displacement is scaled by 1 up to
    innerDistance and by a cosine blend down to 0 at outerDistance. Working values: 1.5 and 10.
  - "test true" switches the force to mass*g only (used for the mesh-only test).
  - accelerationRelaxation / accelerationDamping exist for this mover (default 1.0); not used.
  - PIMPLE entry moveMeshOuterCorrectors defaults to false: the mesh and body then move once per step.
- Fields: U on the cylinder is movingWallVelocity, p stays zeroGradient, pointDisplacement added
  (cylinder calculated, front/back empty, all other patches fixed at 0); fvSolution gets correctPhi and a
  pcorr solver (as in the OpenFOAM 11 wingMotion tutorial).
- Mass: m = m* (pi/4) D^2 L with m* = 2.546, D = 1, L = 0.1 -> m = 0.19996237 (definition provisional: m*
  comes from my summary of Verma and De and is not yet checked against their PDF).
- Scripts: scripts/run/{moving_overlay.sh, set_coupling.sh, make_meshzone_test.sh},
  scripts/analysis/{compare_histories.py, null_test_stats.py, body_motion.py, save_feasibility_results.sh}.
  Results as text: results/feasibility/.

## Test 1: explicit coupling fails
Case moving_Re150_null_medium_dt0.0025: symplectic integrator, nOuterCorrectors 1, spring f_n = 10
(k = 789.4198), restart from t = 100 of the fixed reference.
- The first 60 steps look physical (spring length peak 1.7e-4 at t = 100.06, as expected for a sudden load).
- From about t = 100.16 the spring length grows by roughly 8 % per step (1.9e-4, 5.7e-4 at 100.22, 3.8e-3 at
  100.28, 0.03 at 100.34, 0.27 at 100.38; estimated from samples every 8 steps).
- The run died with a floating-point exception in the pressure solve at t = 100.3975 (step 159), Courant
  number max 1094, body speed 430.
- Reading of the source: with moveMeshOuterCorrectors false, the force of step n moves the body into
  step n+1, and symplectic computes the new position from the old acceleration only (fully explicit).
  The growth is consistent with the added-mass instability of weakly coupled schemes at low mass ratio
  (m* = 2.5). That is a hypothesis: the change that fixed it (Test 2) altered three things at once, and the
  pressure condition on the moving wall was not excluded.

## Test 2: null test (strong coupling, stiff spring)
Case moving_Re150_null_newmark_oc3_medium_dt0.0025: Newmark, nOuterCorrectors 3, moveMeshOuterCorrectors yes,
f_n = 10, restart t = 100, run to t = 120 (2235 s solver time).
- Completed, End, no error hit apart from the sigFpe header; 24000 mover calls = 8000 steps x 3.
- Early differences from the fixed reference are a ring-down, not a defect: dCd, dCl and the spring
  length all peak at f = 8.4 (predicted 8.5 from f_n / sqrt(1 + 0.39), accepted 7-9.5), and they decay
  (dCd amplitude 7.1e-2 -> 2.7e-3 between t = 100.5-110 and 110-120). The restart starts from zero
  displacement with an undamped spring, i.e. a sudden load. Not excluded: a smaller numerical start-up
  artefact underneath.
- Acceptance statistics, window t = 110-120 (criteria set before these statistics were computed, after the
  point-by-point rms had been seen):
  - mean Cd: reference 1.33791, test 1.33581, -0.157 % (tolerance 0.5 %) PASS
  - Cl rms: 0.35180 / 0.34774, -1.154 % (tolerance 2 %) PASS
  - upward Cl zero crossings: 111.3567 / 111.3422 and 116.7322 / 116.7161, shifts -0.0145 and -0.0160
    (tolerance 0.05) PASS
- Limits: window of about 1.9 periods; the body moves only about 1e-4 D, so the large-displacement mesh
  motion is not exercised; one run.

## Test 3: mesh-only test of the zones (no flow)
Case meshzone_i1.5_o10: test true, g = (8 9.8 0), 0.35 time units; body ends at (0.4865, 0.5960)
(analytic 0.49, 0.60). innerDistance 1.5, outerDistance 10.
- checkMesh: aspect ratio 15.377, max skewness 0.80298 and min volume 4.2569e-06 unchanged; non-orthogonality
  max 33.26 -> 33.36 deg, average 5.93 -> 6.30 deg; Mesh OK. No acceptance numbers were set beforehand.

## Test 4: release test (soft spring)
Case moving_Re150_release_Ur5_medium_dt0.0025: Newmark, 3 outer correctors, moveMeshOuterCorrectors yes,
f_n = 0.2 (U_r = 5 in the convention U/(f_n D); definition not yet checked against the literature),
k = 0.315768, zones 1.5 / 10, restart t = 100 (zero displacement), run to t = 160 (6932 s).
- Completed, stable. y maxima: 0.121 (t = 103.8), 0.364, 0.518, 0.573, 0.588, 0.592, ..., 0.5942 (t = 157.2):
  saturated near 0.59 D (last five maxima still creep up by 0.3 %).
- Window t = 130-160 (4 whole body periods, 134.717-155.892): body frequency 0.18891, Cl frequency 0.18881,
  y amplitude 0.5938, mean x 0.32752, x peak-to-peak 0.0544, mean Cd 2.06909, Cl rms 0.28898.
  For comparison the fixed cylinder sheds at about 0.1860 (period 5.3755).
- Force balance in x (criterion 3 %, set before running): k mean(x)/(0.5 Aref) = 2.06842 vs mean Cd = 2.06909,
  -0.03 % PASS. This checks the force transfer and its sign and scale, not the mass.
- Equation of motion, by hand (not scripted): F_y,amp = (k - m w^2) Y = 0.03406 x 0.5938 = 0.02022 ->
  Cl amplitude 0.404; measured sqrt(2) x Cl rms = 0.409 (1.1 % difference, harmonics likely).
- Outer correctors, last step: momentum initial residuals fall pass 1 -> 3 from 5.2e-5 to 4.5e-9 (Ux) and
  6.9e-4 to 5.4e-8 (Uy); the body position changes by about 1e-8 D between mover calls inside the step.
- checkMesh at t = 120, 140, 160: Mesh OK; non-orthogonality max 33.34, 33.29, 33.23 deg, average
  6.19, 6.05, 6.75 deg (undeformed 33.26 / 5.93); body at (0.337, -0.587) at t = 160.

## What is settled
Moving-mesh FSI with sixDoFRigidBodyMotion in OpenFOAM 11 under foamRun is feasible for this problem:
stable, converged within the step, valid mesh at 0.6 D displacement, force balance closes.

## What is not settled
- Which part of the strong-coupling set-up is needed (Newmark, outer correctors, moveMeshOuterCorrectors);
  fewer outer correctors might be enough (cost). Needs an ablation.
- Dependence of the amplitude on dt, mesh, domain and outer correctors; no uncertainty on 0.594 D.
- Comparison with Verma and De (PDF not read yet): m*, U_r, amplitude and frequency definitions.
- Mesh margin beyond 0.6 D displacement.
- The release test started from rest with a relaxed spring: the in-line transient is undamped (zeta = 0).
  The production runs need a start procedure.
- Forced-oscillation stage (approved staging) not done; its parameters need a decision (D10).
- Raw force histories, logs and the restart state 100/ are not tracked; data export still owed.
