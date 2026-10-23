#!/usr/bin/env bash
# set_coupling.sh -- set the fluid-body coupling of a moving-mesh case made by moving_overlay.sh.
#
# Usage:  set_coupling.sh <case> <integrator> <nOuter>
#
#   <integrator>  symplectic | Newmark      (sixDoFRigidBodyMotion solver type)
#   <nOuter>      PIMPLE nOuterCorrectors (integer >= 1)
#                 if > 1, moveMeshOuterCorrectors is set to yes, so that the body motion is
#                 re-solved in every outer corrector (strong coupling by fixed-point iteration);
#                 if 1, the entry is removed (default: no, mesh and body move once per time step).
#
# Edits constant/dynamicMeshDict and system/fvSolution (each edit must match exactly once),
# appends the setting to moving.params, and prints the resulting lines.
# Run with its input closed:   set_coupling.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: set_coupling.sh <case> <integrator> <nOuter>}
integ=${2:?}
nout=${3:?}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

case "$integ" in symplectic|Newmark) ;; *) fail "integrator must be symplectic or Newmark, got $integ" ;; esac
case "$nout" in ''|*[!0-9]*) fail "nOuter must be a positive integer, got $nout" ;; esac
[ "$nout" -ge 1 ] || fail "nOuter must be >= 1"
[ -f "$dir/constant/dynamicMeshDict" ] || fail "no $dir/constant/dynamicMeshDict (run moving_overlay.sh first)"
[ -f "$dir/system/fvSolution" ] || fail "no $dir/system/fvSolution"

/usr/bin/python3 -I - "$dir/constant/dynamicMeshDict" "$dir/system/fvSolution" "$integ" "$nout" <<'EOF' || fail "edit failed"
import re, sys
dmd, fvs, integ, nout = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])

s = open(dmd).read()
s, n = re.subn(r'(solver\s*\{\s*type\s+)\w+(\s*;)', lambda m: m.group(1) + integ + m.group(2), s)
if n != 1:
    sys.exit("dynamicMeshDict: solver type entry matched %d times" % n)
open(dmd, "w").write(s)

f = open(fvs).read()
f, n = re.subn(r'(nOuterCorrectors\s+)\d+(\s*;)', lambda m: m.group(1) + str(nout) + m.group(2), f)
if n != 1:
    sys.exit("fvSolution: nOuterCorrectors matched %d times" % n)
f = re.sub(r'\n[ \t]*moveMeshOuterCorrectors[ \t]+\w+[ \t]*;', '', f)
if nout > 1:
    f, n = re.subn(r'(correctPhi\s+yes\s*;)', lambda m: m.group(1) + '\n    moveMeshOuterCorrectors yes;', f)
    if n != 1:
        sys.exit("fvSolution: correctPhi entry matched %d times" % n)
open(fvs, "w").write(f)
EOF

printf 'integrator %s\nnOuterCorrectors %s\n' "$integ" "$nout" >> "$dir/moving.params"

echo "== dynamicMeshDict"
grep -n -A2 "^    solver" "$dir/constant/dynamicMeshDict"
echo "== fvSolution PIMPLE"
sed -n '/^PIMPLE/,/^}/p' "$dir/system/fvSolution"
echo "RESULT: OK"
