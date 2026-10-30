#!/usr/bin/env bash
# next_chunk.sh -- continue a finished moving-mesh case by one more chunk (restart from its last written time).
#
# Usage:  next_chunk.sh <case_dir> <new_end_time>
#
# Requires: the previous chunk ended with exit code 0 (log.exit), its last logged time equals the controlDict
# endTime, and the endTime directory holds the mesh and body state needed for a restart.
# Does:     log.foamRun -> log.foamRun.<start>-<end>,  log.exit -> log.exit.<start>-<end>;
#           controlDict startTime := old endTime, endTime := <new_end_time>;  launches via launch_case.sh.
# Refuses (and changes nothing) if any check fails. Run with its input closed:  next_chunk.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: next_chunk.sh <case_dir> <new_end_time>}
new=${2:?usage: next_chunk.sh <case_dir> <new_end_time>}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[ -d "$dir" ] || fail "no directory $dir"
dir=$(cd "$dir" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
cd_file="$dir/system/controlDict"

[ -f "$cd_file" ]        || fail "no $cd_file"
[ -f "$dir/log.foamRun" ] || fail "no log.foamRun"
[ -f "$dir/log.exit" ]    || fail "no log.exit (previous chunk not finished?)"
grep -q "exit code 0 " "$dir/log.exit" || fail "previous chunk did not exit with code 0: $(cat "$dir/log.exit")"
[[ "$new" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "new end time must be a number, got '$new'"

[ "$(grep -cE '^startTime[[:space:]]' "$cd_file")" = 1 ] || fail "startTime not found exactly once in controlDict"
[ "$(grep -cE '^endTime[[:space:]]' "$cd_file")" = 1 ]   || fail "endTime not found exactly once in controlDict"
a=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$cd_file")
b=$(awk '/^endTime/   {gsub(";","",$2); print $2}' "$cd_file")

awk -v n="$new" -v b="$b" 'BEGIN{exit !(n+0 > b+0)}' || fail "new end time $new must exceed the current endTime $b"

last=$(grep '^Time = ' "$dir/log.foamRun" | tail -1 | awk '{gsub("s","",$3); print $3}')
awk -v l="$last" -v b="$b" 'BEGIN{exit !(l+0 == b+0)}' || fail "last logged time '$last' is not endTime $b"

[ -d "$dir/$b" ]                                         || fail "no restart directory $dir/$b"
[ -f "$dir/$b/polyMesh/points" ]                         || fail "no moved mesh $dir/$b/polyMesh/points"
[ -f "$dir/$b/uniform/sixDoFRigidBodyMotionState" ]      || fail "no body state in $dir/$b/uniform"
[ ! -e "$dir/log.foamRun.$a-$b" ]                        || fail "$dir/log.foamRun.$a-$b already exists"
[ ! -e "$dir/log.exit.$a-$b" ]                           || fail "$dir/log.exit.$a-$b already exists"
[ ! -d "$dir/postProcessing/forces/$b" ]                 || fail "$dir/postProcessing/forces/$b already exists"

echo "== chunk $a-$b archived; continuing $b -> $new in $dir"
mv "$dir/log.foamRun" "$dir/log.foamRun.$a-$b" || fail "could not rename log.foamRun"
mv "$dir/log.exit"    "$dir/log.exit.$a-$b"    || fail "could not rename log.exit"
sed -i -E "s/^startTime[[:space:]]+[^;]*;/startTime       $b;/" "$cd_file" || fail "sed startTime failed"
sed -i -E "s/^endTime[[:space:]]+[^;]*;/endTime         $new;/" "$cd_file" || fail "sed endTime failed"
grep -E '^(startFrom|startTime|endTime|deltaT)' "$cd_file"

bash "$here/launch_case.sh" "$dir" < /dev/null || fail "launch_case.sh failed (logs are already renamed)"
echo "RESULT: OK"
