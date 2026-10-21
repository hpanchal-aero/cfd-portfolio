#!/usr/bin/env bash
# derive_case.sh -- make a fixed-cylinder case from an existing case, reusing its mesh unchanged.
#
# Usage:  derive_case.sh <src_case> <dst_case> <Re> <deltaT> <endTime> [restart_time]
#
#   - copies <src_case>/constant/polyMesh (and mesh.md5 / mesh.args if present) into <dst_case>
#   - runs setup_fixed.sh for Re, deltaT and endTime (0/, system/ and the two constant files
#     come from cases/_template_fixed)
#   - restart_time (optional): copies the saved time directory <src_case>/<restart_time>
#     into <dst_case> and sets startTime to it (startFrom stays startTime), so that the run
#     restarts from that saved state
#   - writes <dst_case>/mesh.source and removes a stale <dst_case>/log.foamRun
#   - checks the result against <src_case> and prints RESULT: OK or RESULT: FAILED
#
# Refuses to touch a <dst_case> that already has system/ unless FORCE=1.
# Run it with its input closed:   derive_case.sh ... < /dev/null

set -uo pipefail

src=${1:?usage: derive_case.sh <src_case> <dst_case> <Re> <deltaT> <endTime> [restart_time]}
dst=${2:?}
Re=${3:?}
dt=${4:?}
endt=${5:?}
rst=${6:-}

here=$(cd "$(dirname "$0")" && pwd)

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[ -d "$src/constant/polyMesh" ] || fail "no mesh in $src/constant/polyMesh"
if [ -n "$rst" ] && [ ! -d "$src/$rst" ]; then fail "restart state $src/$rst not found"; fi
if [ -e "$dst/system" ] && [ -z "${FORCE:-}" ]; then
    fail "$dst already has system/ (set FORCE=1 to rebuild it)"
fi

mkdir -p "$dst/constant" || fail "cannot create $dst"
rm -rf "$dst/constant/polyMesh"
cp -a "$src/constant/polyMesh" "$dst/constant/polyMesh" || fail "mesh copy failed"
for f in mesh.md5 mesh.args; do
    if [ -f "$src/$f" ]; then cp "$src/$f" "$dst/$f"; fi
done
rm -f "$dst/log.foamRun"

"$here/setup_fixed.sh" "$dst" "$Re" "$dt" "$endt" < /dev/null || fail "setup_fixed.sh failed"

if [ -n "$rst" ]; then
    rm -rf "$dst/$rst"
    cp -a "$src/$rst" "$dst/$rst" || fail "restart copy failed"
    sed -i "s/^startTime .*/startTime       $rst;/" "$dst/system/controlDict" || fail "cannot set startTime"
fi

if [ -f "$src/mesh.md5" ]; then srcmd5=$(cut -c1-8 "$src/mesh.md5"); else srcmd5="none recorded"; fi
printf 'polyMesh copied unchanged from %s\nsource mesh md5 (first 8 chars): %s\ncopied on: %s (UTC)\n' \
    "$src" "$srcmd5" "$(date -u +%F)" > "$dst/mesh.source"

bad=0
chk() { if [ "$2" = 0 ]; then echo "   ok   $1"; else echo "   FAIL $1"; bad=1; fi; }

echo "== checks: $dst against $src"
diff -rq "$src/constant/polyMesh" "$dst/constant/polyMesh" > /dev/null; chk "polyMesh identical" $?
diff -rq "$src/0" "$dst/0" > /dev/null; chk "0/ identical" $?
for f in fvSchemes fvSolution forceCoeffs; do
    diff -q "$src/system/$f" "$dst/system/$f" > /dev/null; chk "system/$f identical" $?
done
re=$(awk '/^nu/ {gsub(";","",$NF); printf "%.4f", 1/$NF}' "$dst/constant/physicalProperties")
[ "$re" = "$(printf '%.4f' "$Re")" ]; chk "1/nu = $re (requested Re $Re)" $?
if [ -n "$rst" ]; then
    diff -rq "$src/$rst" "$dst/$rst" > /dev/null; chk "restart state $rst identical to source" $?
    st=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$dst/system/controlDict")
    [ "$st" = "$rst" ]; chk "startTime = $st (restart time $rst)" $?
    sf=$(awk '/^startFrom/ {gsub(";","",$2); print $2}' "$dst/system/controlDict")
    [ "$sf" = "startTime" ]; chk "startFrom = $sf" $?
fi
nl=$(diff "$src/system/controlDict" "$dst/system/controlDict" | grep -c '^>' || true)
echo "   info controlDict lines changed against the source: $nl"
grep -E '^(deltaT|endTime|startTime|startFrom|writeInterval)' "$dst/system/controlDict" | sed 's/^/   info /'

if [ "$bad" = 0 ]; then echo "RESULT: OK"; else echo "RESULT: FAILED"; exit 1; fi
