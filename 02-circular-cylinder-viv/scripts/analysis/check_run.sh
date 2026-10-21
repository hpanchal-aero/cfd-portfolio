#!/usr/bin/env bash
# check_run.sh -- integrity checks and the standard analysis (window t = 120-180) of one finished run.
#
# Usage:  check_run.sh <case_dir> <json_out>
#
# Prints: solver state, first and last time step in the log, log end, force file and row count,
#         warning-pattern count (1 = the sigFpe header line only), Courant maxima,
#         the force_signal.py summary, and the spread of period, Cl amplitude and mean Cd over the
#         shedding cycles with t_start >= 100 (a saturation check).
# Writes the analysis result to <json_out>. Uses the latest folder in postProcessing/forces/
# (a restarted case has only its restart-time folder).
# Run it with its input closed:   check_run.sh ... < /dev/null

set -uo pipefail

case_dir=${1:?usage: check_run.sh <case_dir> <json_out>}
json=${2:?usage: check_run.sh <case_dir> <json_out>}
here=$(cd "$(dirname "$0")" && pwd)
log="$case_dir/log.foamRun"

[ -f "$log" ] || { echo "ERROR: no log.foamRun in $case_dir" >&2; exit 1; }
fdir=$(ls -d "$case_dir"/postProcessing/forces/*/ 2>/dev/null | sort -V | tail -1)
[ -n "$fdir" ] || { echo "ERROR: no postProcessing/forces in $case_dir" >&2; exit 1; }
dat="${fdir}forceCoeffs.dat"
[ -f "$dat" ] || { echo "ERROR: $dat not found" >&2; exit 1; }

echo "=================== $case_dir"
echo "solvers running now: $(pgrep -x foamRun | wc -l)"
echo "first Time line: $(grep -E '^Time =' "$log" | head -1)"
echo "last Time line:  $(grep -E '^Time =' "$log" | tail -1)"
echo "log end: $(tail -2 "$log" | tr '\n' '|')"
echo "force file: $dat"
echo "force rows: $(grep -vc '^#' "$dat")   first t: $(grep -v '^#' "$dat" | head -1 | awk '{print $1}')   last t: $(grep -v '^#' "$dat" | tail -1 | awk '{print $1}')"
echo "warning-pattern lines (1 = sigFpe header): $(grep -cE 'FOAM (Warning|FATAL)|floating point|nan' "$log")"
echo "Courant max t>=100: $(awk '/^Time =/ {t=$3+0} /Courant Number/ && t>=100 {print $NF}' "$log" | sort -g | tail -1)   whole run (includes the initial field): $(awk '/Courant Number/ {print $NF}' "$log" | sort -g | tail -1)"

out=$(/usr/bin/python3 "$here/force_signal.py" "$dat" --t0 120 --t1 180 --json "$json" 2>&1)
echo "$out" | sed '/per-cycle table/,$d'
echo "$out" | grep -E '^ +[0-9]+\.[0-9]+ +[0-9]' | awk '$1>=100 {n++; if (n==1||$2<p0) p0=$2; if (n==1||$2>p1) p1=$2; if (n==1||$3<a0) a0=$3; if (n==1||$3>a1) a1=$3; if (n==1||$4<d0) d0=$4; if (n==1||$4>d1) d1=$4} END {printf "t>=100 spread (%d cycles): period %s..%s  Cl_amp %s..%s  Cd_mean %s..%s\n", n, p0, p1, a0, a1, d0, d1}'
echo "$out" | grep 'json written'
