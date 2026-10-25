# 09 - Enlarged domains, replicate and restart (Re 150 fixed cylinder)

Date: 2026-10-25. Working note; to be rewritten for readers at the end of the project.

## Runs added (all Re 150, medium mesh resolution, dt = 0.0025, t = 0..200, window t = 120-180)

| case | domain (inlet / outlet / half-height, D) | cells | notes |
|---|---|---|---|
| dom-big | 30 / 60 / 30 | 31288 | ran to t = 200 in 5250 s (baseline: 4037 s); the machine was shared with another project |
| dom-big2 | 45 / 90 / 45 | 36358 | checkMesh OK: max aspect 15.9058, max non-orthogonality 32.9203, max skewness 0.871193 (baseline 0.80298, dom-big 0.693); location of the worst-skewed cell not determined |
| dom-regen | 15 / 30 / 15 (baseline) | same as baseline | cyl_medium_regen.msh (md5 914d2962...), the same regenerated mesh as the Re 100 replicate |

## Domain series (% of the larger-domain value, from verification_table.py 150)

| quantity | y30 | xin30 | xout60 | sum | to dom-big | to dom-big2 | step big -> big2 |
|---|---|---|---|---|---|---|---|
| St | 0.404 | 0.447 | 0.033 | 0.884 | 0.966 | 1.343 | 0.373 |
| mean Cd | 0.373 | 0.565 | 0.120 | 1.058 | 1.516 | 1.983 | 0.460 |
| Cl rms | 0.252 | 0.852 | 0.287 | 1.391 | 2.474 | 2.610 | 0.133 |
| Cl amplitude | 0.252 | 0.833 | 0.264 | 1.349 | 2.490 | 2.631 | 0.138 |

Baseline values: St 0.18603, mean Cd 1.33791, Cl rms 0.36103, Cl amplitude 0.51102.

- The three single-boundary changes add up for St (hand arithmetic: sum 0.81 % of the baseline value against 0.96 % measured for dom-big) but not for the forces: the measured change to dom-big is 1.84 times the sum for mean Cd and 2.98 times for Cl rms (hand arithmetic).
- The series has not converged for St and mean Cd: the step from dom-big to dom-big2 (0.373 % and 0.460 %) is as large as a single-boundary effect. Cl rms is nearly flat (0.133 %).
- Observed only: the step ratio (second / first) is 0.39 for St and 0.30 for Cd, near the 0.33 that a 1/(half-height) scaling would give. Two points, three boundaries moved together; no extrapolation is used.

## Decisions
- D14 (refined): the domain term of the bands is the change from the baseline to the largest domain run (dom-big2), not the sum of the single-boundary changes (D7b), because the sum was smaller than the measured combined change for every quantity. Re 100 has no combined-domain run, so it keeps the D7b sum and the scripts say so.
- D15: one further enlargement (45/45/90) to measure convergence: done (dom-big2).
- D16: one Re 150 replicate: done (dom-regen).
- D17: the U_r sweep keeps 30/30/60; domain sensitivity of A_y* and the response frequency is checked later with one FSI case on 45/45/90.
- D18: dom-regen was interrupted by a WSL crash at t = 165.08 and restarted from the latest saved time (160), at the user's choice (the alternative was a restart from 120).

## Replicate (dom-regen against the baseline)
- Scatter in % of the replicate value: St 0.000, mean Cd 0.002, Cl rms 0.004, Cl amplitude 0.003. This is the reproducibility for identical input. It does not contain the sensitivity to the near-body mesh topology, which changes when the domain extents change: plane point counts inside r < 2 differ by up to 1.6 % between the baseline, dom-big and dom-big2 meshes (8693, 8555, 8713 points), while the boundary-layer ring (r < 0.6) is identical (2928). Whether this contributes to the non-additivity of Cd and Cl rms is untested.
- An earlier expectation (replicate scatter near 1 %) was wrong: it was based on those domain-mesh differences, not on regeneration.

## Restart of dom-regen
- Crash: log and force file truncated with NUL bytes in the last line only; the field files of time 160 contained no NUL bytes. Restart from 160, first part kept as log.foamRun.part1_crash and log.forces.part1_crash.
- stitch_forces.py joins the force records (first part for t < 160, restart from 160); 80001 rows, spacing deviation 2.8e-14, no duplicates. The log was joined the same way (80000 time steps, none out of order).
- Over the overlap t = 160..165.1175 (2048 rows) the restart differs from the first part by at most 9.1e-7 in Cd and 2.43e-6 in Cl (both at the first step, where backward time stepping falls back to first order), rms 2.1e-8 and 5.5e-8, decaying. The overlap is only about one shedding period.

## Validation consequence (validation_st.py)
- Baseline: St 0.18603, +1.420 % from Williamson (0.18342), U_num 1.492 %, band 2.000 %, ratio 0.71, PASS (Re 100: +1.728 %, ratio 0.86, PASS, domain term from the D7b sum).
- Production domain dom-big: +0.449 %, ratio 0.22, PASS (mesh and dt terms taken from the baseline).
- Largest domain dom-big2: +0.076 %, no verdict: its own domain term is not measured and the series had not converged.

## Open items and limitations
- The domain series is not converged for St and mean Cd at 45/45/90.
- Re 100 has no combined-domain run; its domain term is the (smaller) D7b sum.
- Cl rms: the domain term (2.61 %, a decrease of Cl rms) is of the size of the mesh term (2.21 %, an increase on the fine mesh); the two have opposite signs and partly cancel, so neither is quoted alone.
- First launch of dom-big2 stopped silently at t = 14.57 (log ends mid-step, no error text, WSL not restarted, no memory kill in the kernel log, the other project's job started two hours later). Cause unknown. launch_case.sh now writes the solver's exit code to log.exit.
- dom-regen is not reproducible from the repository alone: the restart state (time 160), the raw and stitched force records and the logs are untracked; the result JSON is committed.
- The committed controlDict of dom-regen has startTime 160 (the restart); for a run from scratch set startTime 0.
