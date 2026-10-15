#!/usr/bin/env bash
# run_validation_case.sh -- reproduce one Ahmed-body validation run from the
# tracked case files: mesh -> decompose -> stage 1 -> stage 2 [-> stage 3]
# -> reconstruct.
#
# Usage:
#   run_validation_case.sh CASE_DIR WORK_DIR [--np N] [--mesh-from DIR]
#                          [--stage1-end N] [--stage2-end N] [--stage3-end N]
#
#   CASE_DIR   tracked case, e.g. cases/val25_clr50_40ms (never modified)
#   WORK_DIR   NEW directory outside the repo where everything is run;
#              the script refuses to use an existing path
#   --np N           MPI ranks (default 8; must match decomposeParDict)
#   --mesh-from DIR  copy constant/polyMesh from DIR instead of running
#                    blockMesh + snappyHexMesh (smoke tests only)
#   --stage1-end N   default 1000 (production)
#   --stage2-end N   default 2000 (production)
#   --stage3-end N   optional. Adds a stage 3 from stage-2-end to N in which
#                    the time averaging is RESTARTED (restartOnRestart yes).
#                    The stage-2 averages are moved aside first, so the final
#                    statistics cover stage-2-end..N only. Used for the 35 deg
#                    case (N = 3000), whose 1000-2000 window was not stationary.
#   All stage ends must be multiples of 50 (writeInterval) so the last
#   iteration is written. Any non-default value is NOT a production run.
#
# Stages (same commands as the original runs):
#   blockMesh; snappyHexMesh -overwrite (serial); checkMesh; decomposePar;
#   mpirun foamRun -parallel (stage 1, no averaging);
#   mpirun foamRun -parallel (stage 2, fieldAverage1 over stage-1-end..stage-2-end);
#   [stage 3: averaging files moved to stage2_averages_quarantine/, then
#    mpirun foamRun -parallel with restartOnRestart yes, window stage-2-end..N];
#   reconstructPar -latestTime.
#
# Known limitation: the original stage-1 controlDict was not saved. Stage 1
# is DERIVED from the tracked (stage-2) controlDict by setting endTime and
# removing the fieldAverage1 block. Everything else is the tracked file.
# The original 40 m/s run was split into stage1/stage1b by a manual stop;
# this driver runs stage 1 in one piece. Bit-identical force histories to
# the original runs are therefore not guaranteed and are not claimed.
# The 35 deg stage 3 was originally run by hand with the same edits; this
# option automates those steps but has been exercised only in a smoke test
# unless stated otherwise in the project README.
#
# OpenFOAM 11 must already be sourced in the calling shell.

set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }

NP=8
MESH_FROM=""
S1_END=1000
S2_END=2000
S3_END=""
POS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --np)          NP="$2"; shift 2 ;;
        --mesh-from)   MESH_FROM="$2"; shift 2 ;;
        --stage1-end)  S1_END="$2"; shift 2 ;;
        --stage2-end)  S2_END="$2"; shift 2 ;;
        --stage3-end)  S3_END="$2"; shift 2 ;;
        -h|--help)     sed -n '2,/^# OpenFOAM 11 must already/p' "$0"; exit 0 ;;
        --*)           die "unknown option $1" ;;
        *)             POS+=("$1"); shift ;;
    esac
done
[ "${#POS[@]}" -eq 2 ] || die "usage: $0 CASE_DIR WORK_DIR [options]  (see --help)"
CASE_DIR=$(cd "${POS[0]}" && pwd) || die "CASE_DIR not found"
WORK_DIR="${POS[1]}"

# --- preconditions -----------------------------------------------------
command -v foamRun   >/dev/null || die "OpenFOAM 11 is not sourced (foamRun not found)"
command -v mpirun    >/dev/null || die "mpirun not found"
command -v python3   >/dev/null || die "python3 not found"
[ -e "$WORK_DIR" ] && die "WORK_DIR already exists: $WORK_DIR (choose a new path)"
for d in 0 constant system; do
    [ -d "$CASE_DIR/$d" ] || die "CASE_DIR lacks $d/"
done
[ -f "$CASE_DIR/constant/triSurface/ahmedBody.stl" ] || die "STL missing in CASE_DIR"
case "$S1_END$S2_END$S3_END$NP" in *[!0-9]*) die "numeric options must be integers" ;; esac
[ $((S1_END % 50)) -eq 0 ] && [ $((S2_END % 50)) -eq 0 ] || die "stage ends must be multiples of 50"
[ "$S2_END" -gt "$S1_END" ] || die "stage2-end must exceed stage1-end"
if [ -n "$S3_END" ]; then
    [ $((S3_END % 50)) -eq 0 ] || die "stage3-end must be a multiple of 50"
    [ "$S3_END" -gt "$S2_END" ] || die "stage3-end must exceed stage2-end"
fi
SUB=$(grep -E '^numberOfSubdomains' "$CASE_DIR/system/decomposeParDict" | tr -dc '0-9')
[ "$SUB" = "$NP" ] || die "--np $NP does not match numberOfSubdomains $SUB"
if [ -n "$MESH_FROM" ]; then
    [ -f "$MESH_FROM/constant/polyMesh/points" ] || die "--mesh-from has no constant/polyMesh/points"
    MESH_FROM=$(cd "$MESH_FROM" && pwd)   # absolute: the script cd's into WORK_DIR later
fi
PRODUCTION=1
{ [ "$S1_END" -ne 1000 ] || [ "$S2_END" -ne 2000 ] || [ -n "$MESH_FROM" ]; } && PRODUCTION=0
if [ -n "$S3_END" ] && [ "$S3_END" -ne 3000 ]; then PRODUCTION=0; fi
[ "$PRODUCTION" -eq 1 ] || echo "WARNING: non-default options -> NOT a production run"

# --- fresh work copy (polyMesh and any run output are not copied) --------
mkdir -p "$WORK_DIR"
( cd "$CASE_DIR" && tar cf - --exclude='constant/polyMesh' --exclude='processor*' 0 constant system ) \
    | ( cd "$WORK_DIR" && tar xf - )
touch "$WORK_DIR/case.foam"
cd "$WORK_DIR"
echo "case:  $CASE_DIR"
echo "work:  $WORK_DIR"
echo "start: $(date -u +%FT%TZ)"

run() {
    local name="$1"; shift
    echo "[$(date -u +%T)] $name"
    "$@" > "log.$name" 2>&1 || { echo "FAILED: $name (see $WORK_DIR/log.$name)"; tail -20 "log.$name"; exit 1; }
}

latest_time() { ls -1 processor0 | grep -E '^[0-9.]+$' | sort -g | tail -1; }

derive_controlDict() {   # $1 endTime, $2 strip fieldAverage1 (1/0), $3 restartOnRestart yes (1/0)
    python3 -I - system/controlDict "$1" "$2" "$3" <<'PY'
import re, sys
path, endtime = sys.argv[1], sys.argv[2]
strip, restart = sys.argv[3] == "1", sys.argv[4] == "1"
s = open(path, encoding="utf-8").read()
s, n = re.subn(r'(?m)^(endTime\s+)\d+(\s*;)', r'\g<1>' + endtime + r'\g<2>', s)
assert n == 1, ("endTime matches", n)
if strip:
    assert s.count("fieldAverage1") == 1, "fieldAverage1 count"
    i = s.index("    fieldAverage1")
    j = s.index("{", i)
    depth = 0
    for k in range(j, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                break
    end = s.index("\n", k) + 1
    s = s[:i] + s[end:]
    assert "fieldAverage1" not in s
if restart:
    s, n = re.subn(r'(?m)^(\s*restartOnRestart\s+)no(\s*;)', r'\g<1>yes\g<2>', s)
    assert n == 1, ("restartOnRestart matches", n)
open(path, "w", encoding="utf-8").write(s)
PY
}

# --- mesh ---------------------------------------------------------------
if [ -n "$MESH_FROM" ]; then
    echo "[$(date -u +%T)] copying polyMesh from $MESH_FROM"
    cp -r "$MESH_FROM/constant/polyMesh" constant/polyMesh
else
    run blockMesh blockMesh
    run snappyHexMesh snappyHexMesh -overwrite
fi
run checkMesh checkMesh
grep -q "Mesh OK" log.checkMesh || die "checkMesh did not report 'Mesh OK' (see log.checkMesh)"
grep -E "cells:|Max aspect ratio|Mesh non-orthogonality|Max skewness" log.checkMesh || true

# --- decompose ----------------------------------------------------------
run decomposePar decomposePar -force

# --- stage 1 (no averaging) ----------------------------------------------
cp system/controlDict system/controlDict.stage2.tracked
derive_controlDict "$S1_END" 1 0
cp system/controlDict system/controlDict.stage1.derived
run stage1 mpirun -np "$NP" foamRun -parallel
grep -q '^End' log.stage1 || die "stage 1 did not finish (no 'End' in log.stage1)"
LAST=$(latest_time)
[ "$LAST" = "$S1_END" ] || die "stage 1 latest time is $LAST, expected $S1_END"

# --- stage 2 (fieldAverage1 from stage-1-end) ---------------------------
cp system/controlDict.stage2.tracked system/controlDict
derive_controlDict "$S2_END" 0 0
run stage2 mpirun -np "$NP" foamRun -parallel
grep -q '^End' log.stage2 || die "stage 2 did not finish (no 'End' in log.stage2)"
LAST=$(latest_time)
[ "$LAST" = "$S2_END" ] || die "stage 2 latest time is $LAST, expected $S2_END"

# --- stage 3 (optional): restart the averaging at stage-2-end -------------
if [ -n "$S3_END" ]; then
    QUAR="$PWD/stage2_averages_quarantine"
    moved=0
    for p in processor*; do
        d="$p/$S2_END"
        [ -d "$d" ] || die "missing $d"
        mkdir -p "$QUAR/$p/uniform"
        for f in "$d"/*Mean; do          # UMean, pMean, kMean, *Prime2Mean
            [ -e "$f" ] || continue
            mv "$f" "$QUAR/$p/"; moved=$((moved + 1))
        done
        if [ -f "$d/uniform/fieldAverage1Properties" ]; then
            mv "$d/uniform/fieldAverage1Properties" "$QUAR/$p/uniform/"; moved=$((moved + 1))
        fi
    done
    [ "$moved" -gt 0 ] || die "no averaging files found in processor*/$S2_END to move"
    echo "stage 3: moved $moved averaging files to $QUAR"
    cp system/controlDict.stage2.tracked system/controlDict
    derive_controlDict "$S3_END" 0 1
    cp system/controlDict system/controlDict.stage3.derived
    run stage3 mpirun -np "$NP" foamRun -parallel
    grep -q '^End' log.stage3 || die "stage 3 did not finish (no 'End' in log.stage3)"
    LAST=$(latest_time)
    [ "$LAST" = "$S3_END" ] || die "stage 3 latest time is $LAST, expected $S3_END"
    EXPECT=$((S3_END - S2_END))
    PROPS="processor0/$S3_END/uniform/fieldAverage1Properties"
    echo "averaging state at $S3_END (expected totalIter $EXPECT, not $S3_END):"
    grep -E 'totalIter|totalTime' "$PROPS" || echo "WARNING: no totalIter/totalTime lines in $PROPS"
    grep -E 'totalIter' "$PROPS" | grep -q "$EXPECT" \
        || echo "WARNING: totalIter does not contain $EXPECT -- the averaging restart may have failed"
fi

# --- reconstruct ----------------------------------------------------------
run reconstructPar reconstructPar -latestTime

# --- summary ----------------------------------------------------------------
echo "=== summary ($(date -u +%FT%TZ))"
echo "production run: $([ "$PRODUCTION" -eq 1 ] && echo yes || echo NO)"
LOGS="log.stage1 log.stage2"
[ -n "$S3_END" ] && LOGS="$LOGS log.stage3"
for f in $LOGS; do
    echo "$f: bounding lines = $(grep -c -i bounding "$f" || true), FOAM FATAL = $(grep -c 'FOAM FATAL' "$f" || true)"
done
echo "reconstructed time dirs:"; ls -d [0-9]* 2>/dev/null | sort -g | tr '\n' ' '; echo
echo "mesh md5 (compare with the tracked reference case's local polyMesh):"
( cd constant/polyMesh && md5sum points faces owner neighbour )
echo "postProcessing: $(ls postProcessing | tr '\n' ' ')"
