#!/usr/bin/env bash
# save_coupling_study.sh -- regenerate the coupling-sensitivity result files (plain text).
#
# Usage:  save_coupling_study.sh < /dev/null
#
# Writes under results/feasibility/:
#   coupling_study_body_motion_115-130.txt   body_motion.py output for the baseline and the three completed variants
#   coupling_study_table.txt                 the comparison table with differences against the baseline [%]
#   coupling_sym3_divergence.txt             spring length history of the symplectic case up to its crash
# Reads the cases on this machine (their logs and force histories are not tracked).

set -uo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root" || exit 1
out=results/feasibility
mkdir -p "$out" || exit 1
C=cases

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

base=moving_Re150_release_Ur5_medium_dt0.0025
names=("$base" coupling_Ur5_nO2 coupling_Ur5_nO1 coupling_Ur5_dt0.00125)
for c in "${names[@]}" coupling_Ur5_sym3; do
    [ -f "$C/$c/log.foamRun" ] || fail "missing $C/$c/log.foamRun"
done

txt=$out/coupling_study_body_motion_115-130.txt
: > "$txt"
for c in "${names[@]}"; do
    echo "=========== $c" >> "$txt"
    /usr/bin/python3 -I scripts/analysis/body_motion.py "$C/$c" 115 130 >> "$txt" || fail "body_motion $c"
done

sym=$C/coupling_Ur5_sym3/log.foamRun
{
    echo "coupling_Ur5_sym3 (symplectic, 3 outer correctors): spring length every 6 steps"
    grep -E "^Time = |spring length" "$sym" | awk '/^Time/{t=$3;next} {for(i=1;i<=NF;i++) if($i=="length") L=$(i+1); n++; if(n%18==0) print t, L}'
    echo "last time: $(grep '^Time = ' "$sym" | tail -1)"
} > "$out/coupling_sym3_divergence.txt"

/usr/bin/python3 -I - "$txt" > "$out/coupling_study_table.txt" <<'EOF' || fail "table"
import re
import sys

blocks = open(sys.argv[1]).read().split("=========== ")[1:]
rows = []
for b in blocks:
    name = b.split("\n", 1)[0].strip()

    def g(pat):
        return float(re.search(pat, b).group(1))

    rows.append((name, g(r"frequency ([0-9.]+)"), g(r"y amplitude \(max-min\)/2 = ([0-9.]+)"),
                 g(r"mean x = ([0-9.]+)"), g(r"mean Cd = ([0-9.]+)"), g(r"Cl rms about mean = ([0-9.]+)")))
base = rows[0]
print("window t = 115-130; baseline = %s" % base[0])
print("%-42s %9s %9s %9s %9s %9s" % ("case", "f_body", "A_y", "mean x", "mean Cd", "Cl rms"))
for r in rows:
    print("%-42s %9.5f %9.4f %9.5f %9.4f %9.5f" % r)
print("differences against the baseline [%]:")
for r in rows[1:]:
    print("%-42s %+9.3f %+9.3f %+9.3f %+9.3f %+9.3f"
          % ((r[0],) + tuple(100.0 * (r[i] - base[i]) / base[i] for i in range(1, 6))))
EOF

echo "== written:"
wc -l "$out"/coupling_*.txt
cat "$out/coupling_study_table.txt"
echo "RESULT: OK"
