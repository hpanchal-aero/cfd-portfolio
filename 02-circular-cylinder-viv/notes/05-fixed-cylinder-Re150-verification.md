# Fixed cylinder, Re = 150: verification (mesh, time step, domain)

Working note, written 2026-10-21. 2D laminar incompressible, same numerical set-up as
Re = 100 (notes 03 and 04). Verification only; nothing here is validation, and no
reference value has been read.

## Decision D8 (2026-10-20, option B)

Re = 150 gets its own verification, nothing borrowed from Re = 100: mesh (medium and
fine), time step (dt = 0.00125), and domain (y30, xin30, xout60). Chosen because the
boundary layer is thinner at Re = 150 (thickness scales as Re^-1/2, about 18 % thinner)
and the domain effects at Re = 100 had been predicted wrongly.

## Cases

All meshes are copied unchanged from the Re = 100 cases (polyMesh identical by
`diff -rq`, source recorded in each `mesh.source`). Only nu = 1/150 changes.

| case | mesh | notes |
|---|---|---|
| fixed_Re150_medium_dt0.0025 | medium, 28,663 cells | reference, t = 0-200, dt = 0.0025 |
| fixed_Re150_fine_dt0.0025 | fine, 54,558 cells | t = 0-200, dt = 0.0025 |
| fixed_Re150_medium_dt0.00125 | medium | restart from the reference's saved t = 100 state, dt = 0.00125, to t = 200 |
| fixed_Re150_medium_dt0.0025_dom-y30 | y = +/-30 | t = 0-200 |
| fixed_Re150_medium_dt0.0025_dom-xin30 | x_in = 30 | t = 0-200 |
| fixed_Re150_medium_dt0.0025_dom-xout60 | x_out = 60 | t = 0-200 |

Restart method: `derive_case.sh` copies the reference's `100/` and sets `startTime 100`
with `startFrom startTime` (the template has `startFrom startTime`). At Re = 100 the
restarted case instead has `startTime 0` with `startFrom latestTime` (note 03); both start
from the same saved state. Force output of the restarted case is in `postProcessing/forces/100/`.

## Run integrity

- All six runs: solver finished at t = 200, log ends with `End`, the only match of the
  warning/fatal/floating-point/nan pattern is the sigFpe header line.
- Force rows: 80,001 for each run from t = 0; 80,001 for the restarted run from t = 100
  (first Time line 100.00125).
- Courant maximum for t >= 100: reference 0.273, fine 0.378, y30 0.299, xin30 0.274,
  xout60 0.277, dt 0.00125 0.136 (half of the reference's, as dt is halved). The larger values
  in the whole-run maximum (1.2-1.5) are the initial-field values before the first step.
- Saturation: the reference is periodic from t about 90 (per-cycle Cl amplitude 0.5110 and
  period 5.3755-5.3756 from t about 80 to 200; mean Cd constant to 5 digits). The fine run and
  the domain runs are likewise constant over all cycles from t = 100.
- Restart relaxation (both Re): after the time step is changed at t = 100 the flow relaxes onto
  the new step's limit cycle, each cycle's deviation about 0.4 of the previous one. Re = 150:
  Cl amplitude 0.5098, 0.5085, 0.5080, 0.5079, 0.5078, 0.5077 then constant; Cd 1.33748 to
  1.33665. Re = 100: Cl amplitude 0.3236, 0.3232, 0.3230, 0.3229, 0.3228 then constant; Cd 1.35600
  to 1.35559. The analysis window (t = 120-180, starting at t = 122.1 and 122.85) contains one
  cycle that is 0.0001 off in Cl amplitude: the effect on the window mean is about 0.003 %,
  against a time-step term of 0.6 %. Criterion fixed before the cycles were read: settled if
  the cycles inside the window agree to the last printed digit. Passed at both Re.
- Analysis: whole shedding periods inside t = 120-180 (10 periods at Re = 150, 9 at Re = 100),
  St from zero crossings (FFT agrees), Cl amplitude (max-min)/2.

## Results

Terms in percent of the finer / larger-domain value; `scripts/analysis/verification_table.py <Re>`.

Re = 100 

quantity medium | mesh dt | y30 xin30 xout60 domain | U_num floor headroom dominant
St 0.16717 | 0.070 0.019 | 0.417 0.505 0.028 0.950 | 1.039 2.0 0.96 domain
Cd_mean 1.35650 | 0.092 0.067 | 0.437 0.589 0.062 1.088 | 1.246 3.0 1.75 domain
Cl_rms 0.22952 | 1.635 0.635 | 0.483 1.272 0.128 1.883 | 4.153 10.0 5.85 domain
Cl_amp 0.32478 | 1.604 0.581 | 0.482 1.287 0.085 1.855 | 4.040 - - domain

Re = 150

quantity medium | mesh dt | y30 xin30 xout60 domain | U_num floor headroom dominant
St 0.18603 | 0.109 0.039 | 0.404 0.447 0.033 0.884 | 1.032 2.0 0.97 domain
Cd_mean 1.33791 | 0.303 0.094 | 0.373 0.565 0.120 1.058 | 1.456 3.0 1.54 domain
Cl_rms 0.36103 | 2.207 0.652 | 0.252 0.852 0.287 1.391 | 4.251 10.0 5.75 mesh
Cl_amp 0.51102 | 2.191 0.639 | 0.252 0.833 0.264 1.349 | 4.180 - - mesh


## Findings

1. The floors (St 2 %, Cd 3 %, Cl rms 10 %) decide the agreement bands at both Re, unless a
   reference's own uncertainty exceeds the headroom: about 1 % (St), 1.5-1.75 % (Cd) and 5.8 %
   (Cl rms). Reference uncertainties are not known yet.
2. The mesh term is larger at Re = 150 than at Re = 100 (St 1.6x, Cd 3.3x, Cl rms 1.35x), in the
   direction expected from the thinner boundary layer. Cl is now mesh-dominated at Re = 150.
3. The domain term at Re = 150 is within 0.5 % (absolute, in percent of the value) of its Re = 100
   value for every quantity. The upstream extent remains the largest single term for Cd and Cl.
   xout60 matters more at Re = 150 (Cd 0.12 %, Cl rms 0.29 %) than at Re = 100 (0.06 %, 0.13 %).
4. The time-step terms are of similar size at both Re (Cl rms 0.64-0.65 %, Cd 0.07-0.09 %).
5. Had the Re = 100 domain term been borrowed (decision option A), the totals would have been
   within 0.5 % of the measured ones. That is known only after the measurement.

## Limitations

- No replicate at Re = 150; the Re = 100 replicate scatter (<= 0.005 %) is the only
  indication of the resolution limit and is not measured here.
- No xin60 at Re = 150: the upstream convergence found at Re = 100 (note 04) is not measured
  here, so the xin30 term may understate the upstream effect at Re = 150 too.
- No coarse mesh at Re = 150: no convergence order and no extrapolated mesh error there. At
  Re = 100 the Cl mesh error on the medium mesh was estimated at about 6 % (note 03, an estimate).
- The three domain effects are summed (D7b), which assumes they are additive; no run changes two
  boundaries at once.
- Mesh x time-step interaction untested (fine mesh only at dt = 0.0025).
- Time-step order observed about 0.6-1 at Re = 100 (note 03), so the last halving is not a
  second-order error estimate; at Re = 150 only one halving exists.
- Raw force histories are in `postProcessing/`, which is not tracked; the window results are
  in `results/exploratory/Re150_*_w120-180.json`.

## Notes on earlier records and on process

- The time-step term printed by `verification_table.py` at Re = 100 (St 0.019, Cd 0.067,
  Cl rms 0.635) differs in the last digit from the values quoted in note 03 (0.018, 0.066,
  0.63). This is consistent with truncation in the earlier note against rounding now; it has
  not been verified from the earlier calculation.
- The first attempt to set up and launch the domain and time-step runs (2026-10-20, 16:15 UTC) failed:
  the cases had no `system/` and two did not exist, so no run started, and the start was delayed
  to the next day. The cause was not identified (a long pasted command block; `setup_fixed.sh`
  alone ran correctly). The steps were then moved into `derive_case.sh`, `launch_case.sh`
  and `check_run.sh`, each with its own checks.

## Reproduction

`scripts/run/derive_case.sh <src_case> <dst_case> <Re> <deltaT> <endTime> [restart_time]` makes each
case from its Re = 100 counterpart (the time-step case from the Re = 150 reference with restart time 100);
`scripts/run/launch_case.sh <case>` starts the run; `scripts/analysis/check_run.sh <case> <json>` checks
and analyses it; `scripts/analysis/verification_table.py <Re>` prints the tables above.
