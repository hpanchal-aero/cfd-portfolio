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
