# CFD Portfolio

A structured computational fluid dynamics portfolio focused on building reliable aerospace CFD capability through progressively more challenging problems.

The portfolio moves from canonical external-flow problems toward unsteady flow, three-dimensional aerodynamics, compressible flow, transonic shock interactions, and multi-element aerodynamics.

The objective is not to demonstrate software usage, but to develop the ability to **formulate, solve, verify, validate, and physically interpret CFD problems**.

---

## What This Portfolio Builds

The projects are designed to develop experience across:

* External aerodynamics
* Separated and unsteady flows
* Turbulence modelling
* Three-dimensional wing aerodynamics
* Compressible and supersonic flow
* Shock–boundary-layer interaction
* Multi-element aerodynamics and ground effect
* Wall-bounded turbulence
* Fluid–structure interaction

The sequence is intentional: establish reliable fundamentals first, then introduce increasing physical and numerical complexity.

---

## Project Roadmap

| #  | Project                                                | Status         | Focus                                                                                           |
| -- | ------------------------------------------------------ | -------------- | ----------------------------------------------------------------------------------------------- |
| 01 | [**Ahmed Body**](01-ahmed-body/)                       | 🟡 In progress | External aerodynamics, separated flow, turbulence modelling, mesh independence, drag validation |
| 02 | [**Circular Cylinder VIV**](02-circular-cylinder-viv/) | ⚪ Planned      | Vortex shedding, Strouhal number, unsteady CFD, fluid–structure interaction                     |
| 03 | [**Finite Wing / Wingtip Vortex**](03-finite-wing/)    | ⚪ Planned      | 3D aerodynamics, induced drag, aspect-ratio effects, wingtip vortex formation                   |
| 04 | [**Supersonic Wedge**](04-supersonic-wedge/)           | ⚪ Planned      | Compressible CFD, oblique shock formation, analytical validation                                |
| 05 | [**RAE2822 Transonic Airfoil**](05-rae2822/)           | ⚪ Planned      | Transonic flow, shock–boundary-layer interaction, experimental validation                       |
| 06 | [**F1 Front Wing**](06-f1-front-wing/)                 | ⚪ Planned      | Multi-element aerodynamics, ground effect, downforce/drag trade-offs                            |
| 07 | [**Turbulent Channel Flow**](07-turbulent-channel/)    | ⚪ Planned      | Wall-bounded turbulence, near-wall treatment, y+, turbulence-model comparison                   |

---

## Project Standards

Each project is expected to establish, where applicable:

* A clearly defined engineering question
* Appropriate governing physics and modelling assumptions
* A justified computational domain and mesh
* Appropriate boundary and initial conditions
* Solver and numerical-method justification
* Convergence assessment
* Mesh-independence or grid-sensitivity assessment
* Verification against analytical or numerical references where appropriate
* Validation against experimental or published data where available
* Physical interpretation of the results
* Engineering conclusions and limitations

A converged simulation is not automatically a correct simulation.

Where credible validation data are unavailable, that limitation is documented rather than treated as evidence of accuracy.

---

## Computational Stack

`OpenFOAM 11` · `Gmsh` · `Python` · `PyVista` · `ParaView` · `Git`

Supporting CAD and computational tools are used where required by individual projects.

---

## Reproducibility

Each project is maintained as a self-contained study.

Project-level documentation covers:

* Geometry
* Mesh methodology
* Boundary conditions
* Solver configuration
* Numerical settings
* Verification and validation approach
* Post-processing
* Reproduction procedure

A project should be reproducible from a clean environment using the instructions provided in its repository.

---

## Status

* 🟢 **Complete** — project meets its documented completion standard
* 🟡 **In progress** — active development or investigation is underway
* ⚪ **Planned** — project has not yet begun

Being **In progress** does not imply that the results are validated or that the engineering question has been answered.

---

## Direction

This portfolio provides the CFD foundation for the broader aerospace research program.

The progression is deliberately aligned with the eventual move toward more specialized problems in **hypersonic aerodynamics, aerothermodynamics, thermal management, and fluid–structure interaction**.

The goal is to build CFD capability that can support research — not simply produce CFD visualizations.

---

## Author

**Harsh Panchal**
Aerospace Engineering · Computational Fluid Dynamics · Aerothermodynamics
