# 02 — Validation criteria for the fixed cylinder (fixed before any reference value is read)

Approved by the project owner on 2026-10-18. Applies to Re = 100 and Re = 150.

## State of knowledge when the rule was set
- CFD results existed for Re = 100 on three meshes (dt = 0.005 and 0.0025): St about 0.167, mean Cd
  about 1.357. Re = 150 not yet run.
- No reference value for St, Cd or Cl has been read in this project yet (a value from a source goes
  into any result only after the source itself has been read).
- Disclosure: the author has general prior knowledge of approximate published values. The rule is
  therefore built on numerical uncertainty and floors fixed now, not on closeness to a specific number.

## Quantities
- St = f D / U from the Cl signal (D = 1, U = 1, so St = frequency).
- Mean Cd and Cl rms (amplitude also reported), over a whole number of shedding periods in the
  periodic state.

## Agreement band, per quantity
band = max(floor, U_num + U_ref)
- floors: St 2 %, mean Cd 3 %, Cl rms 10 %.
- U_num: from our own studies at that Re. Sum of the absolute differences caused by the last mesh
  refinement (medium to fine), the last time-step refinement, and the domain-size change. Summing is
  deliberately conservative.
- U_ref: the uncertainty stated by the source, or the spread between independent sources. If none is
  available, U_ref = 0, the floor applies, and the results say so.

## Verdicts
- Must pass: St at Re = 100 and at Re = 150.
- Should pass: mean Cd.
- Reported only, no verdict: Cl rms / amplitude (weakest references, largest mesh sensitivity of
  our own: 1.6 % between medium and fine at Re = 100).

## Kind of reference
- Experimental (for example St against Re): validation against experiment. Experiments are 3D with
  parallel shedding; our model is strictly 2D. State this next to the comparison.
- Other 2D simulations (for example Cd, Cl): code-to-code consistency, not validation against
  experiment. The results must say which is which.

## Rules for use
- A failure is reported as a failure and investigated. The set-up is not tuned to make it agree.
- The floors cannot change after a reference value has been read. Any later change needs a new,
  dated entry here that states the reason.

## 2026-10-19 - domain-size term (decision D7b)
Decided before any domain-size result was read, and before any reference
value was read.
- Domain study: three single-boundary runs on the medium mesh at
  dt = 0.0025 (cross-flow y = +/-30, upstream x_in = 30, downstream
  x_out = 60) plus a regenerated baseline replicate (same extents,
  mesh generated again).
- The domain-size term in the numerical uncertainty is the SUM of the
  absolute changes of the three single-boundary runs relative to the
  baseline, per quantity, expressed like the mesh and time-step terms
  (relative to the value of the larger configuration).
- Replicate scatter is reported next to the domain results as the
  resolution limit. A change smaller than the scatter is flagged
  "not resolved" but is still counted at its measured value. The
  scatter is not an extra term and is not subtracted.
- Floors (St 2 %, mean Cd 3 %, Cl rms 10 %) are unchanged.

## 2026-10-22 - reference for St, compared value, U_ref (clarification; floors unchanged)
Written after the reference source (Williamson 1989, Eq. 6) had been read and after
the baseline St had been seen to lie 1.4-1.7 % above it. It clarifies what the rule
above leaves open; it does not change any floor.
- St reference: C. H. K. Williamson, J. Fluid Mech. 206 (1989) 579-627, Eq. (6),
  St = A/Re + B + C*Re with A = -3.3265, B = 0.1816, C = 1.600e-4 (read from the
  PDF, p. 606).
- Compared value: the baseline configuration (medium mesh, dt = 0.0025, baseline
  domain), the one whose differences define U_num. If the domain effects add up
  (not tested), a domain-enlarged estimate would lie closer to the reference, so
  the baseline is the less favourable choice.
- U_ref for St = 0.06 %, the average percentage error of the fit stated by the
  paper (p. 607). It is a lower bound for the reference uncertainty: the
  measurement uncertainty is not given in the parts of the paper that were read.
- Not read, not used: the Appendix B data tables.
- Mean Cd and Cl rms: no reference chosen yet (decision D9 open).

## 2026-10-23: FSI validation (D10 = A, D11 = C)

D10 = A: no separate forced-oscillation stage. The coupling is verified inside the FSI stage by
sensitivity runs of one free-vibration case (outer correctors, integrator, time step, mesh).

D11 = C: the FSI results are compared with Verma and De (arXiv 2211.03307) in two ways:
1. the tabulated grid-study point of their Table I (Re 150, m* = 2, U_r = 6, zeta = 0, f* = 1;
   finest grid A_y* = 0.536, C_L rms = 0.071; their model is 3D, L/D = 9.6); needs an extra run of
   ours at m* = 2;
2. their m* = 2.546 response curves at Re 150 (Figs. 5-8), digitised from the figures; the
   digitising uncertainty is estimated and added to the reference uncertainty.

Floors, fixed now (the same band rule as above: larger of the floor and numerical plus reference
uncertainty):
- transverse amplitude A_y* = [max(Y/D) + |min(Y/D)|]/2: 5 %, verdict;
- response frequency (transverse, streamwise): 2 %, verdict;
- streamwise amplitude A_x*: reported without verdict (the origin of X in their definition is not
  resolved: from the relaxed spring or from the mean position);
- C_L rms: reported without verdict (small difference of large terms near resonance).
2D (ours) against their 3D model is stated as a limitation of the comparison, not as a floor.

Disclosure: the Table I values above had been read before these floors were written. They were not
used to choose the floors. No other reference value (figure data, tables of other cases) had been read.

## 2026-10-25: domain term (D14 refined), further enlargement (D15), replicate (D16)

The domain term of U_num was defined on 2026-10-19 (D7b, before any domain result was read) as the sum
of the absolute single-boundary changes. At Re 150 the measured change to the combined enlarged domain
(dom-big, 30/30/60 D) was larger than that sum for every quantity (% of the larger-domain value:
St 0.966 against 0.884, mean Cd 1.516 against 1.058, Cl rms 2.474 against 1.391). D14 therefore
becomes: the domain term is the measured change from the baseline to the largest combined-domain run.
After D15 that run is dom-big2 (45/45/90 D); the step dom-big -> dom-big2 (St 0.373 %, mean Cd 0.460 %,
Cl rms 0.133 %) shows that the series had not converged for St and mean Cd.
- Where no combined-domain run exists (Re 100), the D7b sum is kept and the scripts print which basis
  was used.
- Floors are unchanged (St 2 %, mean Cd 3 %, Cl rms 10 %). The compared value of the primary St row is
  still the baseline configuration (fixed before any gap was known). Added: a row for the production
  domain dom-big (mesh and dt terms taken from the baseline, domain term = step to dom-big2) with a
  verdict, and a line for dom-big2 without a verdict (its own domain term is not measured).
- Effect at Re 150: U_num for St 1.032 -> 1.492 %, mean Cd 1.456 -> 2.381 %, Cl rms 4.251 -> 5.470 %.
  No verdict changes (the floor decides each time).

The replicate (D16, regenerated baseline mesh, Re 150) gives the resolution limit for identical input:
St 0.000 %, mean Cd 0.002 %, Cl rms 0.004 %, Cl amplitude 0.003 %. It does not contain the sensitivity
to the near-body mesh topology that changes with the domain extents; that sensitivity is not measured.

Disclosure: the D14 refinement was decided after the dom-big result and the Williamson St gap
(+1.42 % for the baseline) were known. The change makes U_num larger, the verdicts were PASS before
and after, and it is motivated by the measured domain runs, not by the verdicts.
