# Note 12 — Fixed cylinder, Re 150: code-to-code comparison with Henderson (1995), St cross-check (D9 = C, D25 = A)

Written 2026-11-01. Sources supplied by the user as PDFs; numbers below were produced by
scripts/analysis/validation_henderson.py from results/exploratory/Re150_*_w120-180.json.

## 1. Sources and what was read
- R. D. Henderson, "Details of the drag curve near the onset of vortex shedding", Phys. Fluids 7, 2102 (1995) (3-page letter,
  read in full). 2D incompressible Navier-Stokes, spectral-element method, 202 elements, 8th-order polynomials (resolution
  fixed by a convergence study at Re = 190). C_D = 2F/(rho U^2 d l), mean over a shedding cycle for the vortex-shedding
  branch. Table I gives fits: C_Df = a0/Re^a1 (a0 = 2.5818, a1 = 0.4369); C_Dp = a0 - a1 Re^a2 exp(a3 Re)
  (a0 = 1.4114, a1 = 0.2668, a2 = 0.1648, a3 = -3.375e-3). The paper calls them "simple fits to the measured data"; no
  uncertainty is stated. The domain size is not stated in the pages read. Coefficients were read from page images.
- C. H. K. Williamson and G. L. Brown, J. Fluids Struct. 12, 1073-1085 (1998), pages 1-9 of 13 read. Not the 1989 paper of
  note 06. Fits of St = S(Re): Eq. (15) 0.2665 - 1.018/sqrt(Re) and Eq. (13) 0.285 - 1.390/sqrt(Re) + 1.806/Re to Williamson's
  parallel-shedding measurements; Eq. (17) 0.2731 - 1.1129/sqrt(Re) + 0.4821/Re (average error-of-fit 0.0004) and the abstract's
  0.2698 - 1.0271/sqrt(Re) to Henderson's 2D numerical data.

## 2. St cross-check of the experimental reference (Re 150)
Williamson 1989 Eq. (6) (note 06): 0.18342. Eq. (15): 0.18338; Eq. (13): 0.18355 (by hand). Same data, so no independent
information. The 2D numerical fits give 0.18545 (Eq. 17) and 0.18594 (abstract), 1.1-1.4 % above the experiments.

## 3. Mean Cd against Henderson (verdict; floor 3 %, U_ref = 0: no stated uncertainty, so the floor applies)
Henderson fit: C_Df 0.28919 + C_Dp 1.04416 = 1.33336.
| row | Cd (CFD) | mesh | dt | domain | U_num | band | diff | verdict |
|---|---|---|---|---|---|---|---|---|
| baseline (medium, dt 0.0025, baseline domain) | 1.33791 | 0.303 % | 0.094 % | 1.983 % | 2.381 % | 3.0 % | +0.342 % | PASS (0.11 of band) |
| big (dom-big 30/30/60 D) | 1.31794 | 0.303 % | 0.094 % | 0.460 % | 0.858 % | 3.0 % | -1.157 % | PASS (0.39 of band) |
| big2 (45/45/90 D) | 1.31190 | | | | | | -1.610 % | no verdict |
Code-to-code with a 2D simulation, not validation against experiment. Mesh and dt terms of the `big` row are taken from the baseline.

## 4. St against the 2D numerical fits (no verdict)
| row | St (CFD) | vs Eq. 17 (0.18545) | vs abstract (0.18594) |
|---|---|---|---|
| baseline | 0.18603 | +0.314 % | +0.048 % |
| big | 0.18425 | -0.646 % | -0.909 % |
| big2 | 0.18356 | -1.016 % | -1.278 % |
The October verdict (note 06, baseline against Williamson 1989: +1.42 %, band 2.0 %, PASS) is unchanged.

## 5. Reading (observations)
- Enlarging the domain lowers both St and Cd (step big -> big2: St 0.373 %, Cd 0.460 %, not converged).
- St moves toward the experiment (big2: 0.18356 against 0.18342, +0.08 %, by hand) and away from Henderson's 2D data;
  Cd moves away from Henderson's drag. Which domain resembles an unbounded flow is not known, and Henderson's domain is
  not known to me. The domain term (1.98 % of Cd) is the largest part of U_num.
- Cl rms: neither paper gives a lift reference, so Cl rms stays without verdict (note 02): baseline 0.36103.

## 6. Limitations
One source for mean Cd. The coefficients of Henderson's fits were read from page images. U_ref = 0 is a rule of note 02,
not a statement that the reference is exact. The St fits of Williamson & Brown to Henderson's data are second-hand. The window of
each CFD value is t = 120-180 (10 whole periods).

## 7. Reproduce
`/usr/bin/python3 -I scripts/analysis/validation_henderson.py` (and validation_st.py for the Williamson verdict).
