#!/usr/bin/env bash
# launch_case.sh -- start foamRun for one prepared case in the background, detached from the terminal.
#
# Usage:  launch_case.sh <case_dir>
#
# Log: <case_dir>/log.foamRun.
# Refuses a case that is incomplete (missing dictionaries, mesh or fields, or missing the time
# directory it must start from) and a case that already has a log (FORCE=1 overrides the log check).
# Run it with its input closed:   launch_case.sh <case_dir> < /dev/null

set -uo pipefail

case_dir=${1:?usage: launch_case.sh <case_dir>}

fail() { echo "ERROR: $*" >&2; exit 1; }

[ -d "$case_dir" ] || fail "no such case: $case_dir"
for p in system/controlDict system/fvSchemes system/fvSolution constant/physicalProperties \
         constant/momentumTransport constant/polyMesh/points 0/U 0/p; do
    [ -e "$case_dir/$p" ] || fail "$case_dir is incomplete: $p is missing"
done

sf=$(awk '/^startFrom/ {gsub(";","",$2); print $2}' "$case_dir/system/controlDict")
st=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$case_dir/system/controlDict")
if [ "$sf" = "startTime" ] && [ ! -d "$case_dir/$st" ]; then
    fail "startFrom startTime $st, but $case_dir/$st does not exist"
fi

if [ -e "$case_dir/log.foamRun" ] && [ -z "${FORCE:-}" ]; then
    fail "$case_dir/log.foamRun already exists (set FORCE=1 to overwrite it)"
fi

abs=$(cd "$case_dir" && pwd)
nohup setsid bash --noprofile --norc -c "source /opt/openfoam11/etc/bashrc; cd '$abs'; foamRun > log.foamRun 2>&1" \
    < /dev/null > /dev/null 2>&1 &
echo "launched $case_dir (startFrom $sf, startTime $st, pid $!)"
