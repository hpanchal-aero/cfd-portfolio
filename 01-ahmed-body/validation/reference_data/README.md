# Reference Data

This directory contains **no third-party measurement data**. It documents what
reference data the project uses and where to obtain it.

## ERCOFTAC AC1-05 (Ahmed body) -- not redistributed here

The experimental data used for validation come from the ERCOFTAC Classic
Collection, Application Challenge AC1-05 (Ahmed body):

https://kbwiki.ercoftac.org/w/index.php/Test_Data_AC1-05

The page is marked "Application Challenge 1-05 (c) copyright ERCOFTAC 2004".
As of 2026-10-11 the page states no licence, terms of use or redistribution
conditions, and this project has not obtained permission to redistribute the
data. The data files are therefore **not** included in this repository, and no
figure in this repository plots measured points. To reproduce the validation
comparison, download the Experiment 2 files from the ERCOFTAC page into a local
directory outside the repository and pass that location to the scripts in
`scripts/validation/`.

Sources named on the ERCOFTAC page for this test case:

- Ahmed, S.R., Ramm, G. and Faltin, G. (1984). *Some Salient Features of the
  Time-Averaged Ground Vehicle Wake.* SAE Technical Paper 840300.
  https://doi.org/10.4271/840300
- Lienhart, H., Stoots, C. and Becker, S. (2000). Flow and turbulence structures
  in the wake of a simplified car model (Ahmed model). DGLR Fach-Symposium,
  Stuttgart. (Source of the Experiment 2 data, as listed on the ERCOFTAC page.)
- Lienhart, H. and Becker, S. (2003). SAE Technical Paper 2003-01-0656.

## ahmed-front-geo.dat -- removed from tracking (2026-10-11)

This file was a raw point cloud of the Ahmed-body front-nose geometry, headed
"Original Data of S.R. Ahmed, DLR Braunschweig", taken from the ERCOFTAC
collection. It was **never used** for geometry construction: the project uses a
tangent-arc approximation of the nose (`geometry/generate_ahmed_body.py`), as in
most published Ahmed-body CFD studies. Because redistribution rights are not
established, the file is no longer tracked and is listed in `.gitignore`. It
remains present in older commits of the git history (added in f3726d8). An
earlier version of this README cited a Manchester ERCOFTAC address (case082)
for it; that identifier was not re-verified against the current ERCOFTAC page.

## Drag data from Ahmed et al. (1984)

No digitised data file is provided. The drag values quoted in the main README
(Section 10.10) are approximate readings made by eye from the paper's Fig. 4 and
Fig. 15(e), labelled as such, and are not a digitised dataset.
