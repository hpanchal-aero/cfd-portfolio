#!/usr/bin/env bash
# save_feasibility_results.sh -- regenerate the moving-mesh feasibility result files (plain text).
#
# Usage:  save_feasibility_results.sh < /dev/null
#
# Reads the cases (run on this machine; their logs and force histories are not tracked) and writes
#   results/feasibility/null_vs_fixed_history_100-120.txt   point-by-point comparison, null test
#   results/feasibility/null_vs_fixed_stats_110-120.txt     acceptance statistics, null test
#   results/feasibility/release_Ur5_body_motion_130-160.txt body motion and force balance, release test
#   results/feasibility/mesh_quality.txt                    checkMesh summaries, mesh-zone and release runs
# Nothing else is written.

set -uo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root" || exit 1
out=results/feasibility
mkdir -p "$out" || exit 1

C=cases
REF=$C/fixed_Re150_medium_dt0.0025/postProcessing/forces/0/forceCoeffs.dat
NUL=$C/moving_Re150_null_newmark_oc3_medium_dt0.0025/postProcessing/forces/100/forceCoeffs.dat
REL=$C/moving_Re150_release_Ur5_medium_dt0.0025

for f in "$REF" "$NUL" "$REL/log.foamRun"; do
    [ -f "$f" ] || { echo "ERROR: missing $f" >&2; echo "RESULT: FAILED"; exit 1; }
done

py=/usr/bin/python3
$py -I scripts/analysis/compare_histories.py "$REF" "$NUL" 100 120 > "$out/null_vs_fixed_history_100-120.txt" || { echo "RESULT: FAILED (compare_histories)"; exit 1; }
$py -I scripts/analysis/null_test_stats.py "$REF" "$NUL" 110 120 > "$out/null_vs_fixed_stats_110-120.txt" || { echo "RESULT: FAILED (null_test_stats)"; exit 1; }
$py -I scripts/analysis/body_motion.py "$REL" 130 160 > "$out/release_Ur5_body_motion_130-160.txt" || { echo "RESULT: FAILED (body_motion)"; exit 1; }

mq=$out/mesh_quality.txt
: > "$mq"
check() {
    echo "=========== $1 -time $2" >> "$mq"
    bash --noprofile --norc -c "source /opt/openfoam11/etc/bashrc; checkMesh -case $C/$1 -time $2 -allGeometry -allTopology < /dev/null" 2>&1 \
        | grep -E "cells:|Max aspect|non-orthogonality|Max skewness|Min volume|Failed|Mesh OK|incorrectly|negative" \
        | cut -c1-120 >> "$mq"
}
check meshzone_i1.5_o10 0
check meshzone_i1.5_o10 0.35
for t in 120 140 160; do check moving_Re150_release_Ur5_medium_dt0.0025 "$t"; done

echo "== written:"
wc -l "$out"/*.txt
echo "RESULT: OK"
