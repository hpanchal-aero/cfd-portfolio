#!/usr/bin/env bash
# make_all_stills.sh -- re-render the 39 flow figures (13 cases x pressure, speed, vorticity) in the shared dark style.
#
# Usage:  bash scripts/viz/make_all_stills.sh        (3 renders at a time; writes results/figures/<label>/*.png)
# Every case is taken from the dense snapshots (every 0.2 time units, last 20 time units of the case) of the re-runs in
# ~/work_scratch/p02/video/<label> (made by scripts/run/launch_videos.sh), so the picture is at the true top of the swing
# (highest cylinder y, flow_snapshots.py) for every case and the cases are comparable.
# For the modulated cases (U_r 3.5 and 4) the 20 time units are one stretch of the modulation cycle.

set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
cd "$here/../.." || exit 1
V=$HOME/work_scratch/p02/video

CASES="Ur3 $V/Ur3 480.2 500
Ur3.5 $V/Ur3.5 480.2 500
Ur4 $V/Ur4 580.2 600
Ur4.5 $V/Ur4.5 380.2 400
Ur5 $V/Ur5 380.2 400
Ur6 $V/Ur6 380.2 400
Ur6_ms2 $V/Ur6_ms2 480.2 500
Ur7 $V/Ur7 380.2 400
Ur7.5 $V/Ur7.5 380.2 400
Ur7.75 $V/Ur7.75 480.2 500
Ur8 $V/Ur8 680.2 700
Ur11 $V/Ur11 480.2 500
Ur17 $V/Ur17 380.2 400"

echo "$CASES" | xargs -P 3 -L 1 bash -c 'out=$(/usr/bin/python3 -E -P scripts/viz/flow_snapshots.py $1 $0 $2 $3 2>&1); res=$(echo "== $0"; echo "$out" | grep -E "chosen|wake|Error|Traceback|no saved"); echo "$res"'
