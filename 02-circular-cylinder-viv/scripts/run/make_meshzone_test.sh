#!/usr/bin/env bash
# make_meshzone_test.sh -- flow-free mesh-motion test of the rigid inner zone / blend distances.
#
# Usage:  make_meshzone_test.sh <case> <src_case> <innerDistance> <outerDistance> <gx> <gy> <endTime>
#
# Builds <case> (its name must contain "meshzone") from the mesh of <src_case>. The cylinder moves
# under the gravity vector (gx gy 0) with `test true` (force = mass*g, no flow, no spring), so after
# endTime it has moved by about 0.5*g*endTime^2 in each direction. Run it with
#     foamRun            (controlDict selects  solver movingMesh;)
# and inspect the moved mesh with  checkMesh -time <endTime>.
# innerDistance / outerDistance are measured from the cylinder wall (see sixDoFRigidBodyMotionSolver.C).
# Run with its input closed:   make_meshzone_test.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: make_meshzone_test.sh <case> <src_case> <inner> <outer> <gx> <gy> <endTime>}
src=${2:?}
inner=${3:?}
outer=${4:?}
gx=${5:?}
gy=${6:?}
endt=${7:?}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

case "$dir" in *meshzone*) ;; *) fail "case name must contain 'meshzone'" ;; esac
[ -d "$src/constant/polyMesh" ] || fail "no mesh in $src/constant/polyMesh"
for f in system/fvSchemes system/fvSolution constant/physicalProperties constant/momentumTransport; do
    [ -f "$src/$f" ] || fail "missing $src/$f"
done
if [ -e "$dir" ] && [ -z "${FORCE:-}" ]; then fail "$dir exists (set FORCE=1 to rebuild)"; fi

rm -rf "$dir"
mkdir -p "$dir/0" "$dir/constant" "$dir/system" || fail "cannot create $dir"
cp -a "$src/constant/polyMesh" "$dir/constant/polyMesh" || fail "mesh copy failed"
for f in physicalProperties momentumTransport; do cp "$src/constant/$f" "$dir/constant/$f" || fail "copy $f"; done
for f in fvSchemes fvSolution; do cp "$src/system/$f" "$dir/system/$f" || fail "copy $f"; done

cat > "$dir/system/controlDict" <<EOF
FoamFile
{
    format          ascii;
    class           dictionary;
    location        "system";
    object          controlDict;
}

application     foamRun;
solver          movingMesh;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         $endt;
deltaT          0.0025;

writeControl    runTime;
writeInterval   $endt;
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
EOF

cat > "$dir/0/pointDisplacement" <<EOF
FoamFile
{
    format      ascii;
    class       pointVectorField;
    location    "0";
    object      pointDisplacement;
}

dimensions      [0 1 0 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    cylinder
    {
        type            calculated;
        value           uniform (0 0 0);
    }
    front
    {
        type            empty;
    }
    back
    {
        type            empty;
    }
    ".*"
    {
        type            fixedValue;
        value           uniform (0 0 0);
    }
}
EOF

cat > "$dir/constant/dynamicMeshDict" <<EOF
FoamFile
{
    format      ascii;
    class       dictionary;
    object      dynamicMeshDict;
}

mover
{
    type            motionSolver;
    libs            ("libfvMeshMovers.so" "libsixDoFRigidBodyMotion.so");
    motionSolver    sixDoFRigidBodyMotion;

    patches         (cylinder);
    innerDistance   $inner;
    outerDistance   $outer;
    test            true;       // force = mass*g only, no flow

    mass            1;
    centreOfMass    (0 0 0);
    momentOfInertia (1 1 1);
    orientation     (1 0 0  0 1 0  0 0 1);
    angularMomentum (0 0 0);
    g               ($gx $gy 0);
    rho             rhoInf;
    rhoInf          1;
    report          on;

    solver
    {
        type symplectic;
    }

    constraints
    {
        planeConstraint
        {
            sixDoFRigidBodyMotionConstraint plane;
            normal          (0 0 1);
        }
        noRotation
        {
            sixDoFRigidBodyMotionConstraint orientation;
        }
    }

    restraints
    {
    }
}
EOF

echo "== built $dir (inner $inner, outer $outer, g ($gx $gy 0), endTime $endt)"
ls "$dir" "$dir/0" "$dir/constant" "$dir/system"
grep -nE "innerDistance|outerDistance|test|^ *g " "$dir/constant/dynamicMeshDict"
echo "RESULT: OK"
