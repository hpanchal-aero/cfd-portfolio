#!/usr/bin/env bash
# make_sweep_case.sh -- build one pre-stretched-spring FSI case (Re 150, dom-big, medium mesh).
#
# Usage:  make_sweep_case.sh <U_r> <Cd_est> [<m*>]
#
#   <U_r>     reduced velocity (f_n = 1/U_r)
#   <Cd_est>  estimated mean Cd, sets the spring pre-stretch xbar_est = Cd_est*0.05/k (see moving_overlay.sh)
#   <m*>      optional mass ratio, default 2.546 (the U_r sweep). A different value adds the suffix _ms<m*>
#             to the case folder name (for example the Verma & De Table I case: U_r 6, m* 2).
#
# Source: cases/fixed_Re150_medium_dt0.0025_dom-big (restart from t = 200, first chunk ends at t = 300).
# Creates: cases/moving_Re150_Ur<U_r>_dom-big_medium_dt0.0025_pre[_ms<m*>]
# Independent check: mass, stiffness and anchor in constant/dynamicMeshDict are re-derived in Python.

set -uo pipefail

ur=${1:?usage: make_sweep_case.sh <U_r> <Cd_est> [<m*>]}
cdest=${2:?usage: make_sweep_case.sh <U_r> <Cd_est> [<m*>]}
mstar=${3:-2.546}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[[ "$ur" =~ ^[0-9]+(\.[0-9]+)?$ ]]    || fail "U_r must be a positive number, got '$ur'"
[[ "$cdest" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "Cd_est must be a non-negative number, got '$cdest'"
[[ "$mstar" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "m* must be a positive number, got '$mstar'"

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root" || fail "cannot cd to $root"

if [ "$mstar" = "2.546" ]; then sfx=""; else sfx="_ms${mstar}"; fi

src=cases/fixed_Re150_medium_dt0.0025_dom-big
dst=cases/moving_Re150_Ur${ur}_dom-big_medium_dt0.0025_pre${sfx}

[ -d "$src/200" ] || fail "$src/200 not found (restart state)"
[ ! -e "$dst" ]   || fail "$dst already exists"

fn=$(awk -v u="$ur" 'BEGIN{printf "%.10g", 1/u}')

echo "== 1. derive $dst (Re 150, dt 0.0025, endTime 300, restart 200)"
bash scripts/run/derive_case.sh "$src" "$dst" 150 0.0025 300 200 < /dev/null || fail "derive_case.sh failed"

echo "== 2. moving overlay (m* = $mstar, fn = $fn, Cd_est = $cdest)"
MSTAR="$mstar" bash scripts/run/moving_overlay.sh "$dst" "$src" "$fn" "$cdest" < /dev/null || fail "moving_overlay.sh failed"

echo "== 3. coupling: Newmark, 3 outer correctors"
bash scripts/run/set_coupling.sh "$dst" Newmark 3 < /dev/null || fail "set_coupling.sh failed"

echo "== 4. independent check of dynamicMeshDict"
/usr/bin/python3 -I - "$dst" "$ur" "$cdest" "$mstar" <<'EOF' || fail "parameter check failed"
import math, re, sys
case, ur, cd, ms = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
s = open(case + "/constant/dynamicMeshDict").read()
def get(pat):
    mm = re.findall(pat, s)
    if len(mm) != 1:
        sys.exit("pattern %r found %d times" % (pat, len(mm)))
    return float(mm[0])
m_f = get(r'\bmass\s+([-0-9.eE+]+);')
k_f = get(r'\bstiffness\s+([-0-9.eE+]+);')
a_f = get(r'\banchor\s+\(([-0-9.eE+]+)\s+0\s+0\)')
m = ms * math.pi / 4 * 0.1
k = m * (2 * math.pi / ur) ** 2
xb = cd * 0.5 * 0.1 / k
a = -xb if xb > 0 else 0.0
for name, f, e in (("mass", m_f, m), ("stiffness", k_f, k), ("anchor_x", a_f, a)):
    rel = abs(f - e) / max(abs(e), 1e-30)
    print("%-10s file %.8g   expected %.8g   rel diff %.2e" % (name, f, e, rel))
    if rel > 1e-6:
        sys.exit("%s mismatch" % name)
print("m* = %g   xbar_est = %.4f D   (k = %.6g, f_n = %.6g)" % (ms, xb, k, 1 / ur))
EOF

echo "== 5. summary"
grep -E '^(startTime|endTime|deltaT|writeInterval)' "$dst/system/controlDict"
cat "$dst/moving.params"
ls "$dst"
echo "RESULT: OK"
