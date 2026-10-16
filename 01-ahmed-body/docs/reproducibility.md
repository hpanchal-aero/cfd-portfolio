# Reproducibility

*Part of [Project 01: Ahmed body](../README.md).*

## 1. What can be reproduced

| Item | Reproducible from the repository? |
|---|---|
| Meshes of the validation cases (25° and 35°) | Yes. The meshes are rebuilt from tracked geometry and dictionaries, and the rebuilt meshes match the originals byte for byte (checked for the 25° mesh against the frozen case, and for the 35° driver run against the 35° mesh case). |
| The 40 m/s, 25° validation run | Yes, with the driver in section 4. A full reproduction was run and its window statistics agree with the committed numbers (Cd 0.28672, Cl 0.32051 over iterations 1000–2000). The force histories are **not** bit-identical (section 6). |
| The 60 m/s and Tu 0.5 % 25° runs | The case directories are tracked and differ from the 40 m/s case only in the inlet values and speed. They were **not** re-run through the driver. |
| The 35° run | The first 2000 iterations went through the driver. Stage 3 (iterations 2001–3000) was run by hand. The driver's `--stage3-end` option automates those steps and was tested on a short run only. |
| Comparison with ERCOFTAC data | Only after you download the data yourself (section 5). The data are not in the repository. |
| The 0°–35° sweep | The case directories are tracked, but the sweep was not re-run, and it carries the errors listed in [errata.md](errata.md). Raw solver output is not stored. |
| Flow-visualisation videos | The video script is tracked, but its input slices come from the old sweep runs, which are not stored. |

## 2. Environment

The work was done on Windows with WSL2 and Ubuntu.

| Component | Version |
|---|---|
| OpenFOAM | 11 |
| Open MPI | 4.1.6 |
| Python | 3.12.3 (system interpreter, `/usr/bin/python3`) |
| numpy, scipy, pandas, matplotlib | 1.26.4, 1.11.4, 3.0.5, 3.6.3 |
| pyvista, vtk, pillow, trimesh | 0.48.4, 9.6.2, 10.2.0, 5.1.1 |
| ffmpeg (videos only) | 6.1.1 |

The Python versions are pinned in [`../requirements.txt`](../requirements.txt). They were
recorded from the machine that produced the results. A fresh install from that file has
not been tested.

Use `/usr/bin/python3` for the scripts. On the author's machine the `python3` found first
on `PATH` belongs to a conda installation that lacks numpy. Do not run the PyVista
scripts with `python3 -I`: isolated mode hides the user site-packages, and the scripts
then fail to import `pyvista`.

**Cost.** The runs used 8 MPI ranks. The 25° validation run took about 8.5–8.8 s per
iteration, so 2000 iterations take about 4.8 hours, plus about 9 minutes of serial
meshing. The 35° run took 4 h 48 min for 2000 iterations and about 5.5 minutes of
meshing. Stage 3 adds 1000 iterations.

## 3. Tracked cases

| Directory under `cases/` | Purpose |
|---|---|
| `val25_clr50_mesh` | 25° geometry (raised 50 mm), mesh dictionaries; used to build and check the mesh |
| `val25_clr50_40ms` | baseline validation run, 40 m/s, nose turbulence 0.25 % |
| `val25_clr50_60ms` | 60 m/s run, same mesh and turbulence target |
| `val25_clr50_40ms_tu05` | 40 m/s sensitivity run with nose turbulence 0.5 % and νt/ν = 20 |
| `val35_clr50_mesh` | 35° geometry (raised 50 mm), mesh dictionaries |
| `val35_clr50_40ms` | 35° validation run, 40 m/s |
| `slant*_re4*` | the exploratory sweep, see [transient-sweep.md](transient-sweep.md) |

The 25° and 35° surfaces are the same CAD geometry with the slant changed. The 35°
surface was raised with `surfaceTransformPoints "translate=(0 0 0.05)" in.stl out.stl`.
The same command reproduces the 25° surface byte for byte.

## 4. Running a validation case

OpenFOAM 11 must be sourced in the shell first. The driver `scripts/validation/run_validation_case.sh`
copies a tracked case to a new directory **outside** the repository, never modifies the
tracked case, and refuses to reuse an existing working directory. It runs `blockMesh`,
`snappyHexMesh -overwrite`, `checkMesh`, `decomposePar`, two (or three) `foamRun` stages
and `reconstructPar -latestTime`. `--help` prints the full usage.

~~~bash
cd 01-ahmed-body

# 25° baseline (iterations 0-1000 without averaging, 1001-2000 averaged)
scripts/validation/run_validation_case.sh cases/val25_clr50_40ms ~/runs/val25_40ms --np 8

# 35°: the third stage restarts the time averaging at iteration 2000
scripts/validation/run_validation_case.sh cases/val35_clr50_40ms ~/runs/val35_40ms \
    --np 8 --stage3-end 3000
~~~

Options:

- `--np N`: MPI ranks (default 8; it must match `decomposeParDict`).
- `--stage1-end`, `--stage2-end`: defaults 1000 and 2000. Any other value is not a
  production run. All stage ends must be multiples of 50 so that the last iteration is written.
- `--stage3-end N`: adds a stage from the end of stage 2 to N. Before it starts, the
  stage-2 averaging files are moved into `stage2_averages_quarantine/`, and the run
  continues with `restartOnRestart yes`, so the final averages cover only the window
  from stage-2-end to N. The driver prints the expected `totalIter` (N − stage-2-end).
- `--mesh-from DIR`: copy an existing mesh instead of meshing (smoke tests only).

**How to check a run.** After the run, confirm that `fieldAverage1Properties` in the last
time directory reports `totalIter` equal to the length of the averaging window (1000 for
the production runs). Then compute window statistics with the stationarity script. Do not
accept a run because the solver exited normally.

## 5. Analysis and figures

All scripts are run from the case or repository directory with `/usr/bin/python3` and
accept `--help`.

| Script (`scripts/…`) | Purpose |
|---|---|
| `stitch_force_segments.py` | joins force-coefficient files from separate stages into one record |
| `stationarity_report.py` | window statistics, drift/std, sub-window spread |
| `spectral_probe_check.py` | spectral peaks of force and probe signals (Lomb–Scargle) |
| `slice_frame_deviation.py` | frame-to-frame deviation of slice data |
| `validation/sample_ercoftac_y0.py` | samples the CFD at the measured ERCOFTAC points (`--angle 25` or `35`) and computes the criteria |
| `validation/plot_ercoftac_profiles.py` | profile plots against the measured data (local use; output is not committed) |
| `validation/diagnose_slant_layer.py` | CFD-only profiles above the slant surface |
| `validation/check_nose_turbulence.py` | checks the turbulence values reached at the nose |
| `validation/plot_force_history.py` | force histories |
| `validation/plot_centreline_cp.py` | centreline pressure coefficient |
| `validation/compare_slant_wakes.py` | 25° against 35°: reversed-flow extent and pressure-drag decomposition |
| `validation/visualize_validation_slices.py` | symmetry-plane Cp and Ux/U∞ figures |
| `visualization/make_slice_video.py` | videos of the sweep slices (needs sweep output, which is not stored) |

The remaining scripts in `scripts/` were written for the sweep and are described in
their own headers.

**ERCOFTAC data.** The comparison data (AC1-05, Experiment 2) are © ERCOFTAC 2004 with no
stated redistribution terms, so they are not stored here and no committed figure shows
measured points. Download them from the ERCOFTAC page and put them anywhere outside the
repository (the author used `~/ercoftac_data`). `validation/reference_data/README.md`
explains the file layout and the coordinate mapping.

## 6. Known limits of the reproduction

- **Stage 1 is derived.** The original stage-1 `controlDict` was not saved. The driver
  derives it from the tracked stage-2 file by setting `endTime` and removing the
  `fieldAverage1` block. The original 40 m/s run was split in two by a manual stop,
  while the driver runs stage 1 in one piece.
- **Histories differ at the 10⁻⁵ level.** Restarting from written fields (six-digit ASCII)
  perturbs the continuation by about 10⁻⁵ relative. A short test confirmed that the
  iteration-50 force row matches the original and the later rows differ at that level.
  The criterion for reproduction is therefore agreement of window statistics, not of
  histories.
- **Only one case fully reproduced.** The 40 m/s, 25° baseline is the only case
  re-run end to end through the driver.
- **No mesh independence.** Reproducing the numbers does not show that they are mesh
  independent; see the limitations in the validation documents.

## 7. Repository conventions

- Raw solver output is not committed. `.gitignore` excludes `polyMesh` directories and
  numeric time directories (`[1-9][0-9]*/`). That rule also catches result directories
  whose names start with two digits, which is why result directories are named
  `case_40ms` and not `40ms`.
- No ERCOFTAC raw data, digitised copies or figures showing measured points are tracked.
- Commit messages carry no tool attribution.
