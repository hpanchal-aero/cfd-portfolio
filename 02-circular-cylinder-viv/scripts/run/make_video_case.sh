#!/usr/bin/env bash
# make_video_case.sh -- copy a finished moving-mesh case into a scratch folder for a dense-output restart (flow video).
#
# Usage:  make_video_case.sh <src_case> <t_start> <t_end> <write_interval> <dst_case>
#
# Copies 0/, constant/, system/ and the saved state <t_start> (and the small record files) of <src_case> to <dst_case>
# and sets startTime, endTime, writeInterval and writeControl runTime in the new controlDict. Nothing else changes.
# The case is not started: use launch_case.sh. <dst_case> is meant to live outside the repository (large output).

source /opt/openfoam11/etc/bashrc
set -eo pipefail

src=${1:?usage: make_video_case.sh <src_case> <t_start> <t_end> <write_interval> <dst_case>}
t0=${2:?}
t1=${3:?}
wi=${4:?}
dst=${5:?}

fail() { echo "ERROR: $*" >&2; exit 1; }

for p in 0 constant system "$t0"; do
    [ -d "$src/$p" ] || fail "$src/$p not found"
done
[ ! -e "$dst" ] || fail "$dst already exists"

mkdir -p "$dst"
cp -r "$src/0" "$src/constant" "$src/system" "$src/$t0" "$dst/"
for f in moving.params mesh.args mesh.md5 mesh.source; do
    cp "$src/$f" "$dst/" 2>/dev/null || true
done

cd_file="$dst/system/controlDict"
foamDictionary -entry startFrom -set startTime "$cd_file" > /dev/null
foamDictionary -entry startTime -set "$t0" "$cd_file" > /dev/null
foamDictionary -entry endTime -set "$t1" "$cd_file" > /dev/null
foamDictionary -entry writeControl -set runTime "$cd_file" > /dev/null
foamDictionary -entry writeInterval -set "$wi" "$cd_file" > /dev/null

echo "== $dst (from $src, restart $t0)"
for k in startFrom startTime endTime deltaT writeControl writeInterval; do
    echo "   $k $(foamDictionary -entry $k -value "$cd_file")"
done
ls "$dst" | tr '\n' ' '; echo
