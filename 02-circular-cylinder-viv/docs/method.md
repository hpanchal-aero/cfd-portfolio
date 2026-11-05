# Method

This document describes the physical model, the numerical set-up and the definitions used in Project 02: a
circular cylinder in a cross-flow at Re = 150, held fixed and mounted on a spring with two degrees of
freedom. The results and their checks are in the other documents of this folder.

## 1. Problem

A circular cylinder in a uniform stream sheds vortices alternately from its two sides. If the cylinder is
free to move on a spring and the shedding frequency approaches the natural frequency of the mounting, the
cylinder oscillates with large amplitude and the wake locks onto the motion (lock-in).

Question: does OpenFOAM 11 reproduce (a) the shedding of a fixed cylinder (Strouhal number St, mean drag
coefficient, rms lift coefficient) and (b) the lock-in range and the amplitude response of an elastically
mounted cylinder over a range of reduced velocity? The hypothesis, recorded before any run, was that lock-in
occurs around the resonance condition U_r = 1/St (about 6) with the response frequency following the natural
frequency over a range of U_r.

## 2. Parameters and non-dimensionalisation

| Quantity | Value | Comment |
|---|---|---|
| Diameter D | 1 | length scale |
| Free-stream speed U | 1 | velocity scale |
| Density rho | 1 | pressure is the kinematic pressure p/rho |
| Kinematic viscosity nu | 0.006666666667 | Re = U D / nu = 150 (fixed cylinder also at Re = 100) |
| Slab thickness L | 0.1 | one cell in z, front and back patches "empty" |
| Reference area A_ref | D L = 0.1 | |
| Mass ratio m* | 2.546 | m = m* (pi/4) D^2 L = 0.19996237 (rho = 1); m* = 2 for one check case |
| Damping ratio | 0 | undamped |
| Natural frequency f_n | 1 / U_r | same in x and y (isotropic spring) |
| Reduced velocity U_r | U / (f_n D) | computed from U_r = 3 to 17 |

The reduced velocity is changed through the spring stiffness, k = m (2 pi / U_r)^2 for D = U = 1. The flow
speed does not change, so Re stays fixed along the sweep. The natural frequency is that of the body in
vacuum, f_n = sqrt(k/m) / (2 pi); the added mass of the fluid is not included in it, so the frequency of the
coupled response can differ from f_n (it is reported as f / f_n).

The parameter set (m* = 2.546, zero damping, equal natural frequencies, Re = 150) follows the study of Verma
and De (arXiv:2211.03307), read from its abstract and parameter description. Their definitions of m* and U_r
have not been checked against the full text of the paper.

## 3. Governing equations

Fluid: incompressible, Newtonian, laminar, constant properties, on a moving mesh (the equations are solved in
the arbitrary Lagrangian-Eulerian form, with the mesh velocity u_m):

    div u = 0
    du/dt + div( (u - u_m) u ) = - grad p + nu laplacian u

Body: a rigid cylinder of mass m, moving in the x-y plane only (rotation locked), attached to an anchor point
by a linear spring of stiffness k with zero rest length and no damping:

    m x'' = F_x - k (x - x_a)
    m y'' = F_y - k y
    F = integral over the cylinder surface of ( -p n + tau . n ) dS

x and y are the displacements of the centre of the cylinder from its start position, F is the fluid force on
the slab of thickness L. The anchor x_a is explained in section 10; for the fixed cylinder there is no motion.

Force coefficients: C_D = F_x / (0.5 rho U^2 A_ref), C_L = F_y / (0.5 rho U^2 A_ref). Strouhal number
St = f D / U with f the shedding frequency.

## 4. Assumptions

- Two-dimensional, laminar flow, no turbulence model. Re = 150 is below the 3D transition; Verma and De state
  that the shedding is purely 2D for Re < 250.
- Incompressible flow, constant properties.
- Rigid cylinder, two translational degrees of freedom (cross-flow and in-line), isotropic linear spring,
  zero structural damping.
- Uniform inflow; slip walls at the top and bottom of the domain, so the blockage of the domain is a
  modelling effect that is tested (see the verification documents).

## 5. Geometry and computational domains

The cylinder has D = 1 and sits at the origin; the domain is one cell thick in z. Domains (distances in D):

| Name | Inlet | Outlet | Half-height | Blockage 1/(2 half-height) |
|---|---|---|---|---|
| baseline | 15 | 30 | 15 | 3.3 % |
| dom-big | 30 | 60 | 30 | 1.7 % |
| dom-big2 | 45 | 90 | 45 | 1.1 % |

The baseline domain is used for the fixed-cylinder mesh and time-step studies, dom-big for the coupled sweep,
and dom-big2 for the domain-size check of the response.

## 6. Meshes

Generated with Gmsh 4.15.2 (script scripts/meshing/cylinder_mesh.py, driver scripts/meshing/mesh_case.sh):
a structured-quad boundary layer on the cylinder (design values: first layer 0.005 D, growth ratio 1.1,
total thickness 0.15 D), a refined wake box (x from 0 to 20 D, |y| < 2 D), extruded by one layer into
hexahedra. Three resolution levels differ by a linear factor of 1.4 in cell size.

Baseline domain (checkMesh, all hexahedra, Mesh OK):

| Level | Cells | Max non-orthogonality | Avg non-orthogonality | Max aspect ratio | Max skewness |
|---|---|---|---|---|---|
| coarse | 14,440 | 41.4 | 8.4 | 11.3 | 0.63 |
| medium | 28,663 | 33.3 | 5.9 | 15.4 | 0.80 |
| fine | 54,558 | 28.3 | 4.6 | 13.9 | 0.95 |

In the dom-big domain the medium mesh has 31,288 cells and the fine mesh 60,229 cells. The coupled sweep uses
the medium resolution; the fine mesh is used for one check case.

Gmsh does not return bit-identical files between runs: cell count and patches are the same, but quality values
differ in the third digit. The mesh of each case is therefore identified by a checksum (mesh.md5 in the case).

Mesh motion: the displacement of the cylinder is imposed on the mesh as a rigid motion out to 1.5 D from the
wall, blended by a cosine function to zero at 10 D from the wall. In a mesh-only test and in a release test
(displacement up to 0.6 D) checkMesh reported a valid mesh, with the maximum non-orthogonality rising from
33.3 to 33.4 degrees.

## 7. Boundary conditions

| Patch | Velocity U | Pressure p |
|---|---|---|
| inlet | fixed value (1 0 0) | zero gradient |
| outlet | inletOutlet (inflow value 0) | fixed value 0 |
| top, bottom | slip | zero gradient |
| cylinder | noSlip (fixed cylinder); movingWallVelocity (moving cylinder) | zero gradient |
| front, back | empty | empty |

Initial field: U = (1 0.05 0) everywhere; the small transverse component only seeds the shedding
instability. Mesh motion (pointDisplacement): cylinder calculated by the motion solver, front and back empty,
all other patches fixed at zero.

## 8. Numerical method

- Solver: OpenFOAM 11, foamRun with the incompressibleFluid module, laminar.
- Time: second-order backward scheme, time step 0.0025 (D/U units) for the production cases; a smaller step
  and other meshes are used in the verification studies.
- Space: gradients Gauss linear; convection Gauss linearUpwind grad(U); Laplacian Gauss linear corrected;
  interpolation linear; surface-normal gradient corrected.
- Pressure-velocity coupling: PIMPLE with momentum predictor, 2 pressure correctors and 1 non-orthogonal
  corrector per outer iteration. Fixed cylinder: 1 outer corrector. Coupled cases: 3 outer correctors with the
  mesh and the body moved at every outer iteration (moveMeshOuterCorrectors), mesh-flux correction (correctPhi)
  and a pcorr solver.
- Linear solvers: GAMG with Gauss-Seidel smoother for p (relative tolerance 0.01 in the iterations, final
  absolute tolerance 1e-8) and for the mesh-flux correction pcorr (tolerance 0.02); smoothSolver with
  Gauss-Seidel for U (absolute tolerance 1e-8).
- Body: sixDoFRigidBodyMotion, Newmark integration, plane constraint (motion in the x-y plane) and orientation
  constraint (no rotation), linearSpring restraint (zero rest length, zero damping), force taken from the
  patch "cylinder" with rho = 1.
- Output: force coefficients (forceCoeffs on the cylinder, C_D along x, C_L along y, reference length 1,
  reference area 0.1, free-stream speed 1) and the body state are written every time step; fields every 20
  time units.

The fixed-cylinder case on the same mesh and domain differs from the coupled case only in the cylinder
velocity condition, in the extra mesh-flux settings and the number of outer correctors listed above, and in
the additional body-state output.

## 9. Quantities extracted

A window of whole periods is the stretch between the first and the last upward zero crossing of the
mean-removed signal inside a chosen time window.

- Fixed cylinder: St from the upward zero crossings of C_L (cross-checked with an FFT), mean C_D and rms C_L
  over whole periods.
- Coupled cases: transverse amplitude A_y* = (max y - min y) / (2 D) over whole periods; response frequency
  f = N / (t_last - t_first) from the upward crossings of y, reported as f / f_n; in-line amplitude
  A_x* = (max x - min x) / (2 D) over the same periods; mean C_D and rms C_L; the phase between lift and
  displacement, from sinusoid fits to y and C_L at the response frequency (positive phase: lift leads the
  displacement); the path of the centre in the x-y plane.

## 10. Start of the coupled cases

Each coupled case restarts from the t = 200 flow state of the fixed-cylinder run on the same mesh and
domain, with the mesh copied unchanged. The body starts at rest at the origin. The spring anchor is placed
upstream of the start position, at x_a = - C_D,est * 0.5 * A_ref / k, where C_D,est is an estimate of the mean
drag coefficient. The mean in-line spring force then balances the mean drag near the start position, and the
mean in-line displacement stays small over the sweep. Each case is run in chunks of 100 time units until the
amplitude of the response has settled (settling rule: see the README of this project).

## 11. Where the checks are

- Numerical verification of the fixed cylinder: fixed-cylinder-verification.md.
- Coupling choices, the results of the sweep, the comparison with reference data and the limitations: the README of this project.

## 12. Limits of the model

Two-dimensional flow (the reference study is three-dimensional); laminar, single Reynolds number for the
coupled study; zero damping, so the response near resonance is sensitive and can show slow modulations;
isotropic spring only; slip top and bottom boundaries; a single mass ratio in the sweep (one check at m* = 2).
