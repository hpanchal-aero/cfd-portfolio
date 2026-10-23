#!/usr/bin/env bash
# moving_overlay.sh -- turn a derived fixed-cylinder case into a spring-mounted moving-mesh case.
#
# Usage:  moving_overlay.sh <case> <src_case> <fn>
#
#   <case>      case made by derive_case.sh (fixed-cylinder files, restart state in place)
#   <src_case>  the fixed case it was derived from (used only for the printed diffs)
#   <fn>        natural frequency of the spring-mass system, in units of U/D (f_n = 1/U_r)
#
# Changes made (everything else is left as derived):
#   0/U and <startTime>/U      cylinder: noSlip -> movingWallVelocity
#   <startTime>/pointDisplacement   new (cylinder calculated, front/back empty, rest fixedValue 0)
#   constant/dynamicMeshDict   sixDoFRigidBodyMotion, plane + orientation constraints, linearSpring
#   system/fvSolution          + correctPhi yes, + pcorr solver (as in the OpenFOAM 11 wingMotion tutorial)
#   system/controlDict         + #include "sixDoFState"
#   system/sixDoFState         sixDoFRigidBodyState function object
#   moving.params              m, k, fn used
# Mass: m = m* (pi/4) D^2 L with m* = 2.546, D = 1, L = 0.1 (provisional definition, see notes).
# Run with its input closed:   moving_overlay.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: moving_overlay.sh <case> <src_case> <fn>}
src=${2:?}
fn=${3:?}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[ -f "$dir/system/controlDict" ] || fail "no $dir/system/controlDict"
[ -d "$src/system" ] || fail "no $src/system"
[ ! -e "$dir/constant/dynamicMeshDict" ] || fail "$dir already has constant/dynamicMeshDict (already overlaid)"

st=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$dir/system/controlDict")
[ -d "$dir/$st" ] || fail "start-time directory $dir/$st not found"
[ -f "$dir/$st/U" ] || fail "$dir/$st/U not found"

read -r m k < <(awk -v fn="$fn" 'BEGIN{pi=atan2(0,-1); m=2.546*pi/4*0.1; w=2*pi*fn; printf "%.8g %.8g\n", m, m*w*w}')
[ -n "${m:-}" ] && [ -n "${k:-}" ] || fail "could not compute mass and stiffness"

# --- 1. moving-wall velocity condition on the cylinder
for f in "$dir/0/U" "$dir/$st/U"; do
    /usr/bin/python3 -I - "$f" <<'EOF' || fail "U edit failed for $f"
import re, sys
p = sys.argv[1]
s = open(p).read()
pat = re.compile(r'(\bcylinder\s*\{[^}]*?)type\s+noSlip\s*;')
s2, n = pat.subn(r'\1type            movingWallVelocity;\n        value           uniform (0 0 0);', s)
if n != 1:
    sys.exit("expected exactly one cylinder noSlip block in %s, found %d" % (p, n))
open(p, "w").write(s2)
EOF
done

# --- 2. pointDisplacement
cat > "$dir/$st/pointDisplacement" <<EOF
FoamFile
{
    format      ascii;
    class       pointVectorField;
    location    "$st";
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

# --- 3. dynamicMeshDict
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
    innerDistance   ${INNER:-1.5};   // rigid out to this distance from the wall [D]; tested in notes (mesh-zone test)
    outerDistance   ${OUTER:-10};    // blend to zero at this distance from the wall [D]

    mass            $m;     // m* (pi/4) D^2 L, m* = 2.546 (provisional)
    centreOfMass    (0 0 0);
    momentOfInertia (1 1 1);    // rotation is locked by the orientation constraint
    orientation     (1 0 0  0 1 0  0 0 1);
    angularMomentum (0 0 0);
    g               (0 0 0);
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
        spring
        {
            sixDoFRigidBodyMotionRestraint linearSpring;
            anchor          (0 0 0);
            refAttachmentPt (0 0 0);
            stiffness       $k;     // k = m (2 pi fn)^2, fn = $fn
            damping         0;
            restLength      0;
        }
    }
}
EOF

# --- 4. function object for the body state
cat > "$dir/system/sixDoFState" <<EOF
sixDoFRigidBodyState
{
    type        sixDoFRigidBodyState;
    libs        ("libsixDoFRigidBodyState.so");
    angleUnits  degrees;
}
EOF

# --- 5. fvSolution and controlDict
/usr/bin/python3 -I - "$dir/system/fvSolution" "$dir/system/controlDict" <<'EOF' || fail "fvSolution/controlDict edit failed"
import re, sys
fvs, cd = sys.argv[1], sys.argv[2]

s = open(fvs).read()
pcorr = '''solvers
{
    "pcorr.*"
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       0.02;
        relTol          0;
    }
'''
s, n1 = re.subn(r'solvers\s*\{\n', lambda m: pcorr, s, count=1)
s, n2 = re.subn(r'PIMPLE\s*\{\n', lambda m: 'PIMPLE\n{\n    correctPhi              yes;\n', s, count=1)
if n1 != 1 or n2 != 1:
    sys.exit("fvSolution: solvers/PIMPLE blocks not found (%d, %d)" % (n1, n2))
open(fvs, "w").write(s)

c = open(cd).read()
old = '#include        "forceCoeffs"'
if c.count(old) != 1:
    sys.exit("controlDict: forceCoeffs include not found exactly once")
c = c.replace(old, old + '\n    #include        "sixDoFState"')
open(cd, "w").write(c)
EOF

printf 'fn %s\nm %s\nk %s\nm* 2.546 (provisional), L 0.1, D 1\n' "$fn" "$m" "$k" > "$dir/moving.params"

# --- report
echo "== parameters: fn = $fn  m = $m  k = $k"
echo "== diff against $src"
diff "$src/system/fvSolution" "$dir/system/fvSolution"
diff "$src/system/controlDict" "$dir/system/controlDict"
diff "$src/0/U" "$dir/0/U"
diff "$src/$st/U" "$dir/$st/U"
ls "$dir/$st" "$dir/constant" "$dir/system"
echo "RESULT: OK"
