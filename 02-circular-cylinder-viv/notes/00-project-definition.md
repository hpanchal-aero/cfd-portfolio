# Project 02 working notes: definition and decisions

Working notes, written 2026-10-16. They are rewritten into docs/ at the end of the
project. Anything marked UNVERIFIED has not been checked against the source.

## Problem and question

A circular cylinder on springs in a cross-flow sheds vortices. When the shedding frequency
approaches the natural frequency of the structure the cylinder oscillates with large
amplitude and the wake locks onto the motion (lock-in).

Question: does OpenFOAM 11 reproduce (a) fixed-cylinder shedding (St, mean Cd, Cl rms)
and (b) the lock-in range and amplitude response of an elastically mounted cylinder over a
range of reduced velocity?

## Approved decisions

| ID | Decision |
|---|---|
| D1 | Re = 100 and Re = 150 for the fixed cylinder; coupled study at Re = 150 |
| D2 | 2 DOF (cross-flow and in-line), rigid cylinder, m* = 2.546, zeta = 0, equal natural frequencies (f* = 1), U* = 2 to 17 |
| D3 | OpenFOAM rigid-body motion solver (sixDoFRigidBodyMotion) with PIMPLE outer iterations |
| D4 | Mesh deformation with a rigid inner zone around the cylinder; no overset |
| D5 | Try mesh independence. Fixed cylinder: yes (cheap in 2D). Coupled case: three meshes at one U* point near peak amplitude; skip it, and record the limitation, if it turns out expensive |
| D6 | Check that validation data are open before relying on them (done, see below) |

Physics: 2D, laminar, incompressible, transient. Re = 150 is below the 3D transition
(Verma and De call Re = 150 fully 2D and say shedding is purely 2D for Re < 250).

Reduced velocity: U* = U / (f_n D), with the natural frequency changed (not the flow
speed) so Re stays fixed along the sweep. UNVERIFIED that this is how the reference study
varies it; to check when the paper is read in full.

## Staging

1. Feasibility: does sixDoFRigidBodyMotion run with foamRun in OpenFOAM 11, with a
   constraint to two translational DOF and linear springs? (Not confirmed from docs.)
2. Fixed cylinder at Re = 100 and 150: mesh study, time-step study, domain study.
3. Forced oscillation with prescribed motion (tests the moving mesh with no coupling).
4. Free vibration, 1 DOF check if cheap, then 2 DOF.
5. U* sweep at Re = 150.

## Hypothesis (recorded before any run)

Lock-in occurs around the resonance condition U* = 1 / St (about 6 for St near 0.16-0.18),
with the response frequency following the natural frequency over a range of U*. The width
of the range and the peak amplitude are not predicted. For comparison only: Verma and De
place lock-in at 5 <= U_r <= 7 at Re = 150 (taken from their text, not an input to the
set-up).

## Quantities to extract

St, mean Cd, Cl rms, amplitudes Ax/D and Ay/D, response frequency over natural
frequency, phase between lift and displacement, trajectory shape (figure-eight expected
for 2 DOF), wake mode.

## Validation sources (status)

| Source | Use | Status |
|---|---|---|
| Verma and De, arXiv 2211.03307 | 2 DOF, m* = 2.546, zeta = 0, f* = 1, U* = 2 to 17, Re 150 to 1000; OpenFOAM PIMPLE, RK4 structure, inverse-distance mesh motion | Open. Read: abstract and parameters. Amplitude values are in figures; one table value: mean Ay* = 0.536 at Re = 150, U_r = 6 (their grid study at m* = 2). Journal and year not found. |
| Prasanth and Mittal 2008, JFM 594, 463 | 2D, m = 10, Re 60 to 200, frequency tuned to fixed-cylinder shedding at Re = 100 | Paywalled; abstract only. DOF count not stated in the abstract. |
| Placzek, Sigrist, Hamdouni 2009, Computers and Fluids | forced and free oscillation at low Re | HAL blocked my access; open in a browser if wanted. UNVERIFIED content. |
| Williamson 1989, JFM 206 | St against Re for the fixed cylinder | Exists; relation and values not yet extracted. |
| Bao et al. | the reference Verma and De compare against at Re = 150 | UNVERIFIED, not found yet. |

Rule from Project 01 (E5): no number from a source goes into a result or a README until the
source has been read.

## To decide before the runs

- Pass/fail criteria for the fixed-cylinder validation (St, mean Cd, Cl rms) and for the
  amplitude response. These are validation methodology and need approval, and must be
  fixed before the runs.
- The in-line natural-frequency convention and the damping of the in-line motion
  (zeta = 0 assumed in both directions).

## Cost

2D meshes are small, so one fixed-cylinder run takes minutes to an hour. The U* sweep has
about 16 coupled runs at Re = 150; the cost per run is to be measured in stage 4.
