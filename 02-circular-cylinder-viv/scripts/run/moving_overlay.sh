#!/usr/bin/env bash
# moving_overlay.sh -- turn a derived fixed-cylinder case into a spring-mounted moving-mesh case.
#
# Usage:  [MSTAR=<m*>] [INNER=<d>] [OUTER=<d>] moving_overlay.sh <case> <src_case> <fn> [<Cd_est>]
#
#   <case>      case made by derive_case.sh (fixed-cylinder files, restart state in place)
#   <src_case>  the fixed case it was derived from (used only for the printed diffs)
#   <fn>        natural frequency of the spring-mass system, in units of U/D (f_n = 1/U_r)
#   <Cd_est>    optional: estimated mean drag coefficient. If given, the spring is pre-stretched:
#               the anchor is placed upstream at x = -xbar_est, xbar_est = Cd_est * 0.5 * Aref / k
#               (Aref = D*L = 0.1, rho = U = 1), so the body starts at x = 0 in static equilibrium
#               with the mean drag. Default 0 = anchor at the start position (anchor (0 0 0)).
#   MSTAR       environment variable: mass ratio m* = m / (rho (pi/4) D^2 L), default 2.546.
#
# Changes made (everything else is left as derived):
#   0/U and <startTime>/U      cylinder: noSlip -> movingWallVelocity
#   <startTime>/pointDisplacement   new (cylinder calculated, front/back empty, rest fixedValue 0)
#   constant/dynamicMeshDict   sixDoFRigidBodyMotion, plane + orientation constraints, linearSpring
#   system/fvSolution          + correctPhi yes, + pcorr solver (as in the OpenFOAM 11 wingMotion tutorial)
#   system/controlDict         + #include "sixDoFState"
#   system/sixDoFState         sixDoFRigidBodyState function object
#   moving.params              m, k, fn, Cd_est, anchor_x, m* used
# Mass: m = m* (pi/4) D^2 L with D = 1, L = 0.1 (provisional definition, see notes).
# Run with its input closed:   moving_overlay.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: moving_overlay.sh <case> <src_case> <fn> [<Cd_est>]}
src=${2:?}
fn=${3:?}
cdest=${4:-0}
mstar=${MSTAR:-2.546}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[[ "$cdest" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "Cd_est must be a non-negative number, got '$cdest'"
[[ "$mstar" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "MSTAR must be a positive number, got '$mstar'"

[ -f "$dir/system/controlDict" ] || fail "no $dir/system/controlDict"
[ -d "$src/system" ] || fail "no $src/system"
[ ! -e "$dir/constant/dynamicMeshDict" ] || fail "$dir already has constant/dynamicMeshDict (already overlaid)"

st=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$dir/system/controlDict")
[ -d "$dir/$st" ] || fail "start-time directory $dir/$st not found"
[ -f "$dir/$st/U" ] || fail "$dir/$st/U not found"

read -r m k xb ax < <(awk -v fn="$fn" -v cd="$cdest" -v ms="$mstar" 'BEGIN{pi=atan2(0,-1); m=ms*pi/4*0.1; w=2*pi*fn; k=m*w*w; xb=cd*0.05/k; ax=(xb>0)?-xb:0; printf "%.8g %.8g %.8g %.8g\n", m, k, xb, ax}')
[ -n "${m:-}" ] && [ -n "${k:-}" ] && [ -n "${ax:-}" ] || fail "could not compute mass, stiffness and anchor"

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

    mass            $m;     // m* (pi/4) D^2 L, m* = $mstar (provisional definition)
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
            anchor          ($ax 0 0);   // upstream of the start position by xbar_est = $xb (Cd_est = $cdest)
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

printf 'fn %s\nm %s\nk %s\nCd_est %s\nxbar_est %s\nanchor_x %s\nm* %s (provisional), L 0.1, D 1\n' "$fn" "$m" "$k" "$cdest" "$xb" "$ax" "$mstar" > "$dir/moving.params"

# --- report
echo "== parameters: m* = $mstar  fn = $fn  m = $m  k = $k  Cd_est = $cdest  xbar_est = $xb  anchor_x = $ax"
echo "== diff against $src"
diff "$src/system/fvSolution" "$dir/system/fvSolution"
diff "$src/system/controlDict" "$dir/system/controlDict"
diff "$src/0/U" "$dir/0/U"
diff "$src/$st/U" "$dir/$st/U"
ls "$dir/$st" "$dir/constant" "$dir/system"
echo "RESULT: OK"
