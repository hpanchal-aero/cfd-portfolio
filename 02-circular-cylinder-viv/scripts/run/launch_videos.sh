#!/usr/bin/env bash
# launch_videos.sh -- build and start the dense-output re-runs (snapshot every 0.2 time units, last 20 time units of each case).
#
# Usage:  bash scripts/run/launch_videos.sh
# For every row (label, source case, restart time, end time): copy the settled case to ~/work_scratch/p02/video/<label>
# with scripts/run/make_video_case.sh and start it with scripts/run/launch_case.sh. Rows whose scratch folder exists are skipped.
# D28 = B: videos for U_r 3, 3.5, 4.5, 6, 7.75, 8, 17. D29: the 39 stills are taken from these dense snapshots too, so
# U_r 4, 5, 6 (m* = 2), 7, 7.5, 11 are re-run for the still pictures (their videos are not rendered unless asked for).
# Restart time = last saved time of the source case minus 20 (every source run ended with exit code 0).
# U_r 6 was made by hand the same way (380 -> 400).

set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
cd "$here/../.." || exit 1
base=$HOME/work_scratch/p02/video
P=cases/moving_Re150_Ur

CASES="Ur3 ${P}3_dom-big_medium_dt0.0025_pre 480 500
Ur3.5 ${P}3.5_dom-big_medium_dt0.0025_pre 480 500
Ur4 ${P}4_dom-big_medium_dt0.0025_pre 580 600
Ur4.5 ${P}4.5_dom-big_medium_dt0.0025_pre 380 400
Ur5 ${P}5_dom-big_medium_dt0.0025 380 400
Ur6 ${P}6_dom-big_medium_dt0.0025_pre 380 400
Ur6_ms2 ${P}6_dom-big_medium_dt0.0025_pre_ms2 480 500
Ur7 ${P}7_dom-big_medium_dt0.0025_pre 380 400
Ur7.5 ${P}7.5_dom-big_medium_dt0.0025_pre 380 400
Ur7.75 ${P}7.75_dom-big_medium_dt0.0025_pre 480 500
Ur8 ${P}8_dom-big_medium_dt0.0025_pre 680 700
Ur11 ${P}11_dom-big_medium_dt0.0025_pre 480 500
Ur17 ${P}17_dom-big_medium_dt0.0025_pre 380 400"

mkdir -p "$base"
echo "$CASES" | while read -r label src t0 t1; do
    dst="$base/$label"
    if [ -e "$dst" ]; then echo "skip $label (exists)"; continue; fi
    bash scripts/run/make_video_case.sh "$src" "$t0" "$t1" 0.2 "$dst" < /dev/null > /dev/null || { echo "FAILED build $label"; continue; }
    bash scripts/run/launch_case.sh "$dst" < /dev/null
done
