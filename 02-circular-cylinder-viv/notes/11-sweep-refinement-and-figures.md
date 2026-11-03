# Note 11 — Sweep refinement (D23), modulated cases, Table I verdict, flow figures

Written while the D17/D24 run (U_r 6 on the 45/45/90 D domain) was still running. All numbers below were measured
with scripts/analysis/body_motion.py, spectrum_y.py and sweep_summary.py in the session of 2026-10-30 to 2026-11-01.
Interpretation is marked as such. Continues note 10.

## 1. New decisions
- D22 = A: U_r 4 (periodic amplitude modulation) is reported as envelope, high state and cycle mean, not by D19.
- D23 = B: sweep refinement with U_r 3.5, 4.5 and 7.75 (same setup, same rules, cap 600).
- D24 = A: the D17 domain check is U_r 6, m* = 2.546, on the 45/45/90 D domain (fixed run dom-big2, mesh md5 18ce7e3e,
  31288 cells for dom-big, 36358 for dom-big2). make_sweep_case.sh got an optional DOM variable (default dom-big).
- D25 = A: the Re 150 fixed-cylinder Cd / Cl rms comparison needs sources the user supplies; none found so far (section 6).

## 2. D19 results of the new cases (A_y* = (max-min)/2 over whole periods)
| U_r | windows | A_y* | change | f | mean Cd | mean x | verdict |
|---|---|---|---|---|---|---|---|
| 4.5 | [284,342], [342,400] | 0.6208, 0.6213 | +0.08 % | 0.20036, 0.20001 | 2.1766, 2.1710 | 0.0419, 0.0412 | PASS (peak spread 0.3 %, 0.1 %) |
| 7.5 | [250,325], [325,400] | 0.3945, 0.3950 | +0.13 % | 0.13281, 0.13285 | 1.3252, 1.3330 | -0.0053, -0.0025 | PASS (first window still has a force transient) |
| 7.75 | [384,442], [442,500] | 0.3680, 0.3680 | 0.00 % | 0.12892, 0.12892 | 1.2892, 1.2893 | -0.0003 | PASS (earlier windows 0.3604, 0.3677: slow growth up to t = 400) |
| m* = 2, U_r 6 | [384,442], [442,500] | 0.5466, 0.5466 | 0.00 % | 0.16061 | 1.70337 | 0.00096 | PASS (settled from t = 300: 0.5467, 0.5466, 0.5466) |
Windows of U_r 7.5 and 7.75 hold 6 to 9 shedding periods (D19 asks for about 10): the values agree to four digits across
three windows, so I accept them. The x force balance passes (|error| <= 0.13 %) in every window.
U_r 7.75 lies between U_r 7.5 (0.395) and U_r 8 (0.079): the steep drop is between 7.75 and 8 (observation at these points).

## 3. U_r 3.5: regular modulation (reported like U_r 4, D22)
- Peak heights of y (t >= 253): tops (0.316-0.319) at t = 253, 285, 317, 349, 381, 413, 445, 477; bottoms (0.080-0.084) at
  267, 299, 331, 363, 395, 426, 458, 490. Autocorrelation of the peak series: first maximum at lag 32.0 (0.87).
- Spectrum of y over [300, 500]: 0.2190 (A 0.2061), 0.1877 (0.1037), 0.2502 (0.0161). 0.2190 - 0.1877 = 0.0313 = 1/32;
  0.2502 = 2*0.2190 - 0.1877. Amplitude at f_n = 0.2857: 0.0017 (0.8 % of the main peak).
- Interpretation (not tested): two close response frequencies beat with a period of 32 (about 7 shedding periods); 0.1877
  is close to the response frequency of U_r 5 (0.1873) and may be the fixed-cylinder shedding frequency (not yet compared).
- Reported values: envelope 0.080 to 0.319; high state 0.319; mean of the peaks over whole cycles 0.2122 ([284,380)) and
  0.2125 ([380,476)), i.e. 0.2124 +/- 0.0002. The sweep table gives 0.2123 for [284,476).
- Mean Cd and Cl rms depend on the window phase (Cd 1.402, 1.441, 1.419, 1.417 in the four windows used); the value in the
  sweep table (1.4459 for [284,476]) is above all of them and is not trusted beyond about 1-2 %.
- No more chunks were needed (8 regular cycles).
- Same caution for U_r 4: table Cd 1.6745 for [250,552] against 1.6655 and 1.6688 for its two halves.

## 4. Sweep table (scripts/analysis/sweep_summary.py, results/sweep/sweep_summary.csv)
Windows are the final verified windows. A_y* of U_r 3.5 and U_r 4 is the highest peak; the lowest peak and the cycle mean
are in the CSV.
| U_r | A_y* | f | f/f_n | mean Cd |
|---|---|---|---|---|
| 3 | 0.0633 | 0.1914 | 0.574 | 1.3568 |
| 3.5 | 0.3183 (low 0.080, mean 0.212) | 0.2193 | 0.767 | 1.4459 (uncertain) |
| 4 | 0.6156 (low 0.330, mean 0.485) | 0.1921 | 0.769 | 1.6745 (uncertain) |
| 4.5 | 0.6213 | 0.2000 | 0.900 | 2.1710 |
| 5 | 0.6048 | 0.1873 | 0.937 | 2.0319 |
| 6 | 0.5369 | 0.1622 | 0.973 | 1.7063 |
| 7 | 0.4481 | 0.1415 | 0.990 | 1.4361 |
| 7.5 | 0.3950 | 0.1328 | 0.996 | 1.3330 |
| 7.75 | 0.3680 | 0.1289 | 0.999 | 1.2893 |
| 8 | 0.0792 | 0.1663 | 1.331 | 1.2374 |
| 11 | 0.0654 | 0.1710 | 1.881 | 1.2581 |
| 17 | 0.0590 | 0.1728 | 2.938 | 1.2657 |
| 6 (m* = 2) | 0.5466 | 0.1606 | 0.964 | 1.7034 |
Observations (no mechanism tested): the largest response is at U_r 4.5, not at U_r 5; mean Cd peaks with it; f/f_n rises
from 0.90 to 0.999 between U_r 4.5 and 7.75; between U_r 7.75 and 8 the amplitude falls from 0.368 to 0.079 and f/f_n jumps
from 0.999 to 1.33. For U_r >= 8 the frequency is 0.166 to 0.173, close to the shedding frequency.
For the modulated cases f is the mean frequency of the upward y crossings (two frequencies are present).

## 5. Table I of Verma & De (m* = 2, U_r 6, Re 150), verdict under D11
Our A_y* = 0.5466 against 0.536: +2.0 %. The band is the larger of the 5 % floor and the numerical plus reference
uncertainty, so it is at least 5 %: A_y* PASS. The numerical terms for the FSI amplitude (mesh, time step, domain) are not
yet measured (domain: D24 run in progress), so the agreement is consistency, not a quantified accuracy.
Response frequency: Table I has none (the 0.1620 derived earlier is my inference from its C_L,rms and A_y*), so no verdict;
a frequency comparison needs the digitised response curves (D11). A_x* and C_L,rms: no verdict (ours 0.0962 against 0.072).
Source of the Table I values: a tool summary of arXiv 2211.03307, not the PDF itself.

## 6. Fixed-cylinder literature search (D9)
UPDATE 2026-11-01: superseded. The user supplied Henderson (1995) and Williamson & Brown (1998); see note 12 (Cd PASS +0.342 %, band 3 %).
Checked, none with Re 150 values: arXiv 2309.08882 (Re 30, 100, 185, 200, 300, 500), the 2025 two-cylinder study in FDMP
(Re up to 160, single-cylinder comparison only in a figure), a PubMed table that was blocked by a browser check. The Verma &
De PDF was not on the session allowlist. No Re 150 reference value for fixed-cylinder mean Cd or Cl rms is available yet.

## 7. Flow figures (scripts/viz/flow_snapshots.py, results/figures/<label>/{pressure,velocity,vorticity}.png)
- PyVista 0.48.4 (user site, so run with python -E -P, not -I). The reader gives the moved mesh: at t = 500 of U_r 7.75 the
  cylinder patch centre (0.00436, -0.21446) equals the logged centre of mass (0.0043637, -0.214455).
- Same window for all cases: x -6 to 15, y -6 to 6 (D = 1); lighting off; limits set from the 13 snapshots:
  pressure +/-1.3 (observed -1.272 to 0.780), speed 0 to 1.7 (max 1.652), vorticity +/-3.5 (wake 99.5 % values 2.05 to 3.18).
  The limits cover these snapshots only. Pressure is p/rho of the solver (with U = 1 the picture shows p/(rho U^2) = Cp/2).
- Snapshot per case: among the saved times of its last 100 units the one where the cylinder is highest (caption gives the y).
  Saved times are 20 apart; for U_r 4.5 (period 5.000) all six samples are at the same phase, the "highest" is y = -0.593,
  half a cycle from the others. U_r 3.5 and U_r 4 show one frame of their modulation cycle.
- U_r 7.75 at t = 420 (checked by eye): shear layers of the right sign (negative above, positive below), alternating vortices,
  stagnation pressure at the front, suction in the near wake and at the vortex cores.

## 8. Run notes
- Fifth power cut: logs stopped 2026-10-30 08:34 UTC (boot 10:05): m* = 2 (389.52) restarted from 380, U_r 7.5 (294.465)
  from 280; both restart directories had no NUL bytes; continuity of m* = 2: dx = -6.1e-5, dy = -2.5e-4 (expected -6.1e-5, -2.6e-4).
- Reboots after clean chunk ends did no damage (exit code 0, no NUL tails).
- Chunk time at three jobs: about 6.5 to 6.8 h per 100 units; one job alone about 3.8 h (D24 run, estimate from progress).
- recover_chunk.sh and next_chunk.sh have mode 644; call them with bash.

## 9. Open items
- D24 run (U_r 6, 45/45/90 D): domain effect on A_y* and f.
- Re 150 fixed-cylinder reference values (D25 = user supplies sources).
- Final pass of sweep figure (break the line across the modulated cases, hollow markers for them), figure comparison
  pictures, README, commit of scripts and figures, publication only at project completion.

## 10. D24 result (appended 2026-11-01): domain effect on U_r 6 (45/45/90 D against 30/30/60 D); closes the D17/D24 item of section 9
Case: moving_Re150_Ur6_dom-big2_medium_dt0.0025_pre (m* = 2.546, Cd_est 1.71 for the spring pre-stretch, anchor -0.38990661),
chunks 200-300, 300-400, exit code 0, no power cut. D19 on [284,342] and [342,400]:
| window | A_y* | f | mean Cd | Cl rms | mean x | peak spread |
|---|---|---|---|---|---|---|
| [284,342] | 0.5383 | 0.16211 | 1.70156 | 0.09236 | -0.00194 | 0.02 % |
| [342,400] | 0.5382 | 0.16212 | 1.70159 | 0.09233 | -0.00193 | 0.00 % |
Change in A_y*: -0.02 %: PASS. x force balance -0.00 % in both windows.
Against the 30/30/60 D case (U_r 6, [342,400]: A_y* 0.5369, f 0.16221, mean Cd 1.70630, Cl rms 0.09029; my arithmetic):
A_y* +0.24 %, f -0.06 %, mean Cd -0.28 %, Cl rms +2.3 % (no verdict).
Limits: (1) the domain and the spring pre-stretch both differ between the two runs (mean x -0.002 against -0.074); the two
effects are not separated. (2) One case in the regular part of the sweep; near the steep drop (U_r 7.75 to 8) and in the
modulated cases the sensitivity may be larger; not measured. (3) The mesh and time-step terms of A_y* are not measured on the
FSI model; the D11 band is at least the 5 % floor, so the Table I verdict (PASS, +2.0 %) is unchanged.

## 11. D26 result (appended 2026-11-03): mesh effect on U_r 6 (fine against medium mesh, same 30/30/60 D domain)
Cases: fixed_Re150_fine_dt0.0025_dom-big (60229 cells, mesh built with MESH_TAG=big, args --x-in 30 --x-out 60 --y-half 30; medium dom-big has 31288),
run 0-200 (exit 0, 18230 s); then moving_Re150_Ur6_dom-big_fine_dt0.0025_pre (made with MESH=fine make_sweep_case.sh 6 2.03: same spring as the
medium reference, anchor -0.46287159, Cd_est 2.03), chunks 200-300 (28515 s) and 300-400 (29808 s), both exit 0, single job. checkMesh fine:
max aspect 14.0, non-orthogonality max 29.5, skewness max 0.688 (medium dom-big: 15.9, 32.9, 0.693).
Fixed fine run, window 120-180: mean Cd 1.32171, Cl rms 0.36166, St 0.1844; 18 cycles from t = 100 saturated (period 5.4220-5.4222).
D19 on [284,342] (8 whole periods) and [342,400] (9 whole periods); same windows as the medium reference, shorter than 10 cycles:
| window | A_y* | f | mean Cd | Cl rms | mean x |
|---|---|---|---|---|---|
| [284,342] | 0.5357 | 0.16219 | 1.70179 | 0.08930 | -0.07485 |
| [342,400] | 0.5356 | 0.16219 | 1.70181 | 0.08928 | -0.07485 |
Change in A_y* -0.02 %: PASS. Peak spread t = 288-399: 0.5358-0.5359 (0.02 %). x force balance -0.00 % in both windows.
Against the medium reference (U_r 6, [342,400]: A_y* 0.5369, f 0.16221, mean Cd 1.70630, Cl rms 0.09029; my arithmetic):
A_y* -0.24 %, f -0.01 %, mean Cd -0.26 %, Cl rms -1.1 % (no verdict). Mesh term of A_y* about 0.24 %, below the 5 % floor: Table I verdict unchanged.
Limits: (1) two meshes only: a sensitivity, not an error bound; no order of convergence. (2) One case in the regular part of the sweep; the steep
region (U_r 7.75 to 8) and the modulated cases may be more sensitive; not measured. (3) The time-step term of A_y* is not measured (dt 0.0025 on both meshes).
(4) The medium reference values are taken from the settled run recorded in the notes, not re-run.

## 12. Correction (appended 2026-11-03), D27 = A
Sections 10 and 11 say the time-step term of A_y* is "not measured" (and section 10 also says the mesh term is not measured). Both are wrong as written:
(a) the mesh term was measured afterwards (section 11: fine against medium, A_y* -0.24 %);
(b) an FSI time-step test exists in note 08 (U_r 5, Newmark, 3 outer correctors, medium mesh, dt 0.0025 against 0.00125, window t = 115-130, 2 whole periods):
A_y -0.017 %, f +0.021 %, mean x -0.015 %, mean Cd -0.015 %, Cl rms +0.31 %; x force balance within 0.04 %.
I wrote "not measured" without re-reading note 08.
Limits of that test (note 08): amplitude not saturated in the window (growth timing mixed with the steady amplitude); the dt 0.00125 case restarts from
a dt 0.0025 state (possible start-up transient); one halving only (no order of convergence); U_r 5 on the earlier release set-up and the smaller domain,
not the settled sweep set-up. Indirect support: fixed cylinder, Re 150, time-step terms Cl rms 0.64-0.65 %, Cd 0.07-0.09 % (note 05).
D27 = A: this test stands as the FSI time-step evidence; no new run.
Numerical terms of A_y* (indicative, three different cases): domain 0.24 % (U_r 6, 45/45/90 D, section 10), mesh 0.24 % (U_r 6, fine, section 11),
time step 0.02 % (U_r 5, note 08); simple sum about 0.5 % (my arithmetic). None is measured at the Table I point (m* = 2), so this is an indicative size,
not a formal uncertainty budget. D11 band for A_y* = larger of 5 % and (numerical + reference uncertainty, U_ref = 0): 5 %. Table I A_y* (+2.0 %): PASS.
The +2.0 % is larger than the numerical terms, so it is not explained by them; its origin is not tested.
