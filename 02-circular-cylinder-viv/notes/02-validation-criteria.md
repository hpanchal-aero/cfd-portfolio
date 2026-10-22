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
