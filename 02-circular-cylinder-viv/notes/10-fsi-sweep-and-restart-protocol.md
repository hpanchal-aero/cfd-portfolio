# Note 10 — FSI sweep (Re 150, 2-DOF, m* = 2.546): results so far, findings, restart protocol

Status at the time of writing: U_r 3, 5, 6, 7, 8, 11, 17 settled by D19. U_r 4 not settled (intermittent).
U_r 7.5 and the m* = 2 (Table I) case are running. Written while runs were in progress; numbers below are
measured values from `scripts/analysis/body_motion.py` and `spectrum_y.py`.
Re-measured with body_motion.py on 2026-10-30: U_r 3, 5, 6, 7, 8, 11, 17 rows. NOT re-measured: U_r 4, section 4 spectra, section 7 m* = 2 values (cases still running at the time of writing).

## 1. Setup of the sweep
- Re 150, laminar, D = U = 1, enlarged domain (30 D / 30 D / 60 D), medium mesh, dt = 0.0025.
- Two degrees of freedom, zeta = 0, f_n = 1/U_r, m* = 2.546 (m = 0.19996237 for L = 0.1), Aref = D*L = 0.1.
- Newmark, 3 outer correctors (D12). Spring: linearSpring, restLength 0.
- All cases restart from the fixed-cylinder state at t = 200 and run in chunks of 100 time units (D19).
- Spring pre-stretch (D20 = B): anchor upstream at x = -Cd_est*0.05/k so the body starts near its static
  equilibrium. Cd_est is an estimate; the measured mean Cd decides the residual offset of the mean x.

## 2. Equivalence of the two spring forms (control, U_r 5)
| | anchor at start (A) | pre-stretched (B) |
|---|---|---|
| A_y* [250, 300] | 0.6035 | 0.6034 |
| frequency | 0.18763 | 0.18763 |
| mean Cd | 2.03702 | 2.03702 |
| Cl rms | 0.32507 | 0.32510 |
| mean x | 0.32249 | 0.00077 |
| force balance k(mean x - anchor)/(0.5 Aref) vs mean Cd | -0.02 % | -0.01 % |
Both are equivalent at U_r 5. This only tests the small-displacement case, which is why D20 = B is kept for large U_r.

## 3. Sweep results (D19: A_y* of two successive windows of about 10 cycles; pass = change <= 1 %)
A_y* = (max - min)/2 over whole periods, which matches the definition of Verma & De
(((Y/D)max + |(Y/D)min|)/2, from a tool summary of the paper; the typeset equation was not read).
| U_r | Cd_est | A_y* (window 1 -> 2) | change | f | mean Cd | Cl rms | mean x | D19 |
|---|---|---|---|---|---|---|---|---|
| 3 | 1.32 | 0.0635 -> 0.0633 [384-500] | -0.3 % | 0.19142 | 1.35676 | 0.52470 | 0.00210 | PASS |
| 4 | 1.70 | modulated: envelope 0.33-0.616, high state 0.614, cycle mean of peaks 0.479 / 0.490 [250-400, 400-552] | D19 not applicable (D22) | 0.1923 / 0.1915 | 1.6655 / 1.6688 | 1.32 / 1.37 | -0.0035 / -0.0031 | modulated, reported per D22 |
| 5 | 2.03 | 0.6045 -> 0.6048 [287-340, 346-399] (form A) | +0.05 % | 0.18731 | 2.03190 | 0.33489 | 0.32172 | PASS |
| 6 | 2.03 | 0.5370 -> 0.5369 [284-400] | -0.02 % | 0.16221 | 1.70630 | 0.0903 | -0.0738 | PASS |
| 7 | 1.47 | 0.4481 -> 0.4481 [285-398] | 0.00 % | 0.14149 | 1.436 | 0.0210 | -0.0105 | PASS |
| 7.5 | 1.34 | running | | | | | | |
| 8 | 1.50 | 0.0798 -> 0.0792 [588-645, 645-697] | -0.75 % | 0.1663 | 1.2375 | 0.1062 | -0.1064 | PASS at t = 700 (D21) |
| 11 | 1.50 | 0.0654 -> 0.0654 [384-500] | 0.0 % | 0.17102 | 1.25806 | 0.15367 | -0.1854 | PASS |
| 17 | 1.50 | 0.0590 -> 0.0590 [284-400] | 0.0 % | 0.17282 | 1.26574 | 0.17427 | -0.4288 | PASS |
The measured mean Cd differs from Cd_est by up to 0.26 (U_r 8: 1.237 against the estimate 1.50). The residual mean x equals
(Cd - Cd_est)*0.05/k in each case, so the pre-stretch behaves as designed. At U_r 8 the measured Cd (1.237) is below the
fixed-cylinder value (1.318), which contradicted my assumption that Cd stays between 1.32 and 1.71.
Force balance in x passes (|error| <= 0.15 %) in every window of every case.

## 4. U_r 8: a slowly decaying free vibration at about f_n
- D19 failed at t = 600 (-3.5 % between [484, 542] and [542, 600]: 0.0835 -> 0.0806); the cap was raised to 700 for this case (D21).
- Spectrum of y over 150-unit windows (strongest peak = shedding-driven response at 0.1663):
  | window | amplitude near f_n = 0.125 (peak at 0.122-0.123) | shedding peak |
  |---|---|---|
  | [260, 410] | 0.0357 | 0.0782 |
  | [410, 560] | 0.0057 | 0.0786 |
  | [450, 600] | 0.00356 | 0.07865 |
  | [550, 700] | 0.00094 | 0.07865 |
- The peak near f_n decays with an e-folding time of about 80-90 time units; the shedding-driven amplitude is constant.
  The (max - min)/2 amplitude is the sum of the two, so it keeps drifting while the driven response is settled.
- Predictions made before the later spectra were measured (decay model): 0.035 and 0.006 (measured 0.0357, 0.0057),
  0.0035 (measured 0.00356), 0.0011 (measured 0.00094).
- With zeta = 0 the only damping of this free vibration is aerodynamic. The peak frequency is about 2 % below f_n; no
  explanation for that offset has been established.

## 5. Force-implied amplitude (check, valid for harmonic steady motion at zeta = 0)
F_amp = (k - m w^2) A, with F_amp = C_L,rms * sqrt(2) * 0.5 * Aref. The difference k - m w^2 is small near resonance, so
C_L,rms is very sensitive to the response frequency. Checks: U_r 6 (m* 2): formula frequency 0.16054 against measured
0.16061; U_r 3, 11, 17: implied amplitudes 0.0631, 0.0656, 0.0591 against measured 0.0633, 0.0654, 0.0590.
Consequence: a 0.9 % difference in response frequency corresponds to about 30 % in C_L,rms. C_L,rms is not a good validation
quantity at zeta = 0, consistent with D11 giving it no verdict.

## 6. U_r 4: periodic amplitude modulation (D19 not applicable; reported per D22 = A)
Record t = 200 to 600 (peaks of y, from body_motion.py). Plateau (peaks >= 0.61) centred at about 250, 400 and 552, so the
modulation period is about 150 time units (about 29 shedding periods). High-state peaks: 0.6144 (t = 250), 0.6156 (t = 400),
0.6126 (t = 552). Collapse starts at about 270, 420 and 566 and has the same shape each time (0.60, 0.55, 0.48 within about
10 units). The low state is not identical in the cycles: minimum peak 0.330 (t = 355) in cycle 1, 0.371 (t = 511) in cycle 2.
Reported values (D22): envelope 0.33 to 0.616; high state 0.614 +/- 0.002; cycle mean of the y peaks 0.4789 for [250, 400)
and 0.4900 for [400, 552), i.e. 0.484 +/- 0.006 (the spread of two cycles, not a statistical error).
Whole-period window values: [250, 400]: A_y* (max-min)/2 = 0.6146 (this is the high state, not an average), f 0.19234,
mean Cd 1.6655, Cl rms 1.32073, mean x -0.00349; [400, 552]: 0.6132, f 0.19149, mean Cd 1.6688, Cl rms 1.36843, mean x -0.00314.
Force balance in x passes in both (+0.00 %, +0.01 %).
Earlier spectra: [200, 300] one peak at 0.2068; [300, 400] peaks at 0.1884 and 0.2106; amplitude at f_n = 0.25 is 0.009 and
0.004, so a free vibration at f_n is not evident (spectra from the earlier record, not re-measured).
Not tested: whether the modulation is physical or numerical (mesh, time step, domain); no comparison with the literature.
The other sweep cases do not show it. Stated as an observation only.


## 7. Table I of Verma & De (arXiv 2211.03307), as read from a tool summary of the PDF
Grid study at Re = 150, zeta = 0, f* = 1, U_r = 6, m* = 2 (stated for this study; the rest of the paper uses 2.546),
3D grids with z/D 0 to 9.6. Columns: C_L,rms | % change | A_y* | % change.
Grid-3 (3,411,828 cells): C_L,rms 0.072, A_y* 0.536; Grid-4 (6,463,859): 0.071, 0.536.
The paper states that its 3D results are identical to its 2D results at Re = 150 and that the wake is two-dimensional there.
Our m* = 2 run (first chunk, window [245, 295]): A_y* 0.5470 (+2.1 % against 0.536), f 0.16061, mean Cd 1.7033,
C_L,rms 0.0962. D19 for this case is pending (chunk 2 running); no verdict yet.
Implied response frequency of the paper from its C_L,rms and A_y* (section 5 formula): about 0.1620 against our 0.1606.

## 8. Run-time measurements and power cuts
- Seconds per step: 0.30 (one job), 0.42-0.43 (three jobs), 0.6-0.8 (five jobs, including the other project's job).
- Power cuts (UTC): 2026-10-27 09:11 (five cases, back to t = 340); 2026-10-28 04:44 (U_r 8 at 577, restart 560);
  2026-10-29 03:06 (U_r 4, 7 at about 330, restart 320); 2026-10-29 19:04 (U_r 8 at 697 restart 680; m* = 2 at 295, restart 280).
  Each left only NUL bytes at the end of the log and of the postProcessing files, and intact time directories.

## 9. Restart protocol (scripts in scripts/run)
- `next_chunk.sh <case> <new_end>`: after a clean end (log.exit code 0 and last logged time = endTime) renames
  log.foamRun and log.exit to log.foamRun.<a>-<b>, sets startTime/endTime, launches.
- `recover_chunk.sh <case> <restart_time>`: after an interruption, cuts a NUL tail and any partial last line from the log and
  the postProcessing files, renames the log, sets startTime and launches. The restart directory must be free of NULs.
- `body_motion.py` reads all log chunks (later logs override the same times) and uses each forces folder only up to the next
  folder's start time, so repeated stretches after a recovery are not counted twice.
- Continuity check after every restart: the first state differs from the last by about the average velocity * dt;
  seen to 3-4 digits in every restart so far.
- The first time step after a restart is first-order in time (backward scheme).

## 10. Open items
- U_r 4 beyond t = 400; U_r 7.5; m* = 2 case D19 and its verdict (A_y* floor 5 %, frequency floor 2 %).
- Fixed-cylinder Cd, Cl and St against published 2D values (D9 = C).
- One FSI case on the 45/45/90 D domain (D17).
- Flow visualisations for every case; export of the restart states and results so the cases are reproducible.
