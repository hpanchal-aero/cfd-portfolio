# Fixed cylinder: Strouhal-number validation against Williamson (1989)

Working note, written 2026-10-22. Validation of St at Re = 100 and Re = 150 under the rule in
note 02 (including its 2026-10-22 clarification). Mean Cd and Cl rms are not covered here.

## What was read

- C. H. K. Williamson, "Oblique and parallel modes of vortex shedding in the wake of a circular
  cylinder at low Reynolds numbers", J. Fluid Mech. 206, 579-627 (1989). The PDF is openly
  downloadable from the Caltech repository (licence: no commercial reproduction); it was
  downloaded to a scratch folder outside this repository and is not committed.
- Read from the text layer of the PDF: the Figure 14 caption and Eq. (6) (p. 606), the text after
  Eq. (6) with the fit errors (p. 607), the introduction (range of the laminar regime), and the
  paragraph on Figure 15 (comparison with 2D numerical computations).
- Eq. (6): St = A/Re + B + C*Re, A = -3.3265, B = 0.1816, C = 1.600e-4, a least-squares fit to the
  parallel-shedding data; root-mean-square error 0.000089 and average percentage error 0.06 %
  (p. 607). The paper introduces it "for the purpose of comparison with two-dimensional numerical
  computations". The paper states the laminar shedding regime as Re = 49 to 178 in the present study.
- Not used: Appendix B data tables (the column headers are not legible in the text layer, and some
  columns are oblique-shedding data).
- Remarks of the paper worth keeping in mind: published St-Re curves differed by almost 20 %, the
  frequency is highly sensitive to three-dimensional effects, and two 2D numerical curves of 1989
  lay 5-15 % above and below its experiments for reasons it states are not known.

## Other sources surveyed (decision D6: are the data open?)

- Verma and De, arXiv 2211.03307 (the coupled reference): data available only "upon reasonable
  request"; the amplitude response at Re = 150 is given only in figures (U_r = 2-12); it gives no
  fixed-cylinder St, Cd or Cl.
- Norberg, J. Fluids Struct. 17(1), 57-96: no open full text on the record page; not read.
- Not usable or not read: the DFG benchmark at Re = 100 (confined channel), a 2026 arXiv paper on
  numerical lift data (the fetch returned an empty PDF), other arXiv papers with 2D cylinder results.

## Method

band = max(floor 2 %, U_num + U_ref); compared value = baseline (medium mesh, dt = 0.0025, baseline
domain); U_num = mesh + time step + domain terms (notes 03-05); U_ref = 0.06 % (stated fit error,
a lower bound). `scripts/analysis/validation_st.py`.

## Result

Re St_ref St_cfd diff % | mesh dt domain U_num U_ref band % | |diff|/band verdict
100 0.16434 0.16717 +1.728 | 0.070 0.019 0.950 1.039 0.06 2.000 | 0.86 PASS
150 0.18342 0.18603 +1.420 | 0.109 0.039 0.884 1.032 0.06 2.000 | 0.71 PASS

St passes at both Reynolds numbers. The FFT value agrees with the zero-crossing value to 0.001 %.

## Reading

- The band equals the floor at both Re (U_num + U_ref is 1.10 % and 1.09 %).
- The CFD value lies above the experiment at both Re by a similar amount (+1.7 %, +1.4 %): a
  systematic offset, not noise. The cause is not known. The domain is the largest numerical term;
  each of the y30 and xin30 runs lowered St by about 0.4-0.5 % (xout60 raised it by 0.03 %). If the
  three changes add up (not tested), enlarging all extents would move St by about -0.9 % at
  Re = 100 and -0.8 % at Re = 150, toward the reference. This is a hypothesis; it was not used
  for the verdict, which follows the rule with the baseline value.
- The Re = 100 pass uses 86 % of the band.

## Limitations

- The experiments are 3D with parallel shedding; the model is strictly 2D. The paper itself says
  the frequency is sensitive to three-dimensional effects.
- U_ref is the fit error of the paper, not the full measurement uncertainty.
- One reference for St. No comparison for mean Cd, Cl rms or amplitude yet (decision D9 open).
- The comparison uses one window per case (nine or ten whole periods in t = 120-180).

## Next

Test of additivity of the domain effects (one run with all three enlarged extents) is possible if
wanted; it would also inform the choice of the production domain.
