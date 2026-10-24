#!/usr/bin/env bash
# make_coupling_study.sh -- build the coupling-sensitivity cases of the U_r = 5 release test.
#
# Usage:  make_coupling_study.sh < /dev/null
#
# All cases: Re 150, spring f_n = 0.2 (U_r = 5), m* = 2.546, zones 1.5 / 10, restart from t = 100 of the
# fixed Re 150 reference, run to t = 130. Each differs from the release run
# (Newmark, nOuterCorrectors 3, dt 0.0025) in one setting:
#   coupling_Ur5_nO2         nOuterCorrectors 2
#   coupling_Ur5_nO1         nOuterCorrectors 1 (moveMeshOuterCorrectors removed)
#   coupling_Ur5_sym3        symplectic integrator
#   coupling_Ur5_dt0.00125   deltaT 0.00125
# Refuses to overwrite an existing case.

set -uo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root" || exit 1

R=cases/fixed_Re150_medium_dt0.0025
fn=0.2
endt=130
rst=100

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }
[ -d "$R/$rst" ] || fail "restart state $R/$rst not found"

step() {  # label, then the command
    local label=$1
    shift
    local out
    out=$("$@" < /dev/null 2>&1)
    case "$out" in
        *"RESULT: OK"*) ;;
        *) echo "$out" >&2; fail "$label" ;;
    esac
}

build() {  # name dt integrator nOuter
    local name=$1 dt=$2 integ=$3 nout=$4
    local dst=cases/$name
    [ ! -e "$dst" ] || fail "$dst already exists"
    step "derive $name" scripts/run/derive_case.sh "$R" "$dst" 150 "$dt" "$endt" "$rst"
    step "overlay $name" scripts/run/moving_overlay.sh "$dst" "$R" "$fn"
    step "coupling $name" scripts/run/set_coupling.sh "$dst" "$integ" "$nout"
    echo "built $name"
}

names=(coupling_Ur5_nO2 coupling_Ur5_nO1 coupling_Ur5_sym3 coupling_Ur5_dt0.00125)
build coupling_Ur5_nO2 0.0025 Newmark 2
build coupling_Ur5_nO1 0.0025 Newmark 1
build coupling_Ur5_sym3 0.0025 symplectic 3
build coupling_Ur5_dt0.00125 0.00125 Newmark 3

echo "== summary"
for c in "${names[@]}"; do
    echo "-- $c"
    grep -hE "^(startTime|endTime|deltaT)" "cases/$c/system/controlDict" | tr -s ' ' | paste -sd' '
    grep -hE "type (Newmark|symplectic)|stiffness|innerDistance|outerDistance" "cases/$c/constant/dynamicMeshDict" | tr -s ' ' | paste -sd' '
    grep -hE "nOuterCorrectors|moveMeshOuterCorrectors" "cases/$c/system/fvSolution" | tr -s ' ' | paste -sd' '
done
echo "RESULT: OK"
