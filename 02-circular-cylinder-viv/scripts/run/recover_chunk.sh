#!/usr/bin/env bash
# recover_chunk.sh -- restart an interrupted moving-mesh chunk (power cut, crash) from a given written time directory.
#
# Usage:  recover_chunk.sh <case_dir> <restart_time>
#
# Requires: no running foamRun in the case, no log.exit (a chunk that ended cleanly is continued with next_chunk.sh),
# a restart directory <restart_time> without NUL bytes, startTime < restart_time < endTime.
# Does:     in log.foamRun and every file under postProcessing: removes a NUL tail (only where the NUL run is the end
#           of the file) and then a partial last line (any final line without a newline), whether or not NULs were found;
#           log.foamRun -> log.foamRun.<startTime>-<restart_time>; controlDict startTime := restart_time
#           (endTime unchanged); launches via launch_case.sh.
# Refuses (and changes nothing, except the file cleaning once it has started) if any check fails.
# Run with its input closed:  recover_chunk.sh ... < /dev/null

set -uo pipefail

dir=${1:?usage: recover_chunk.sh <case_dir> <restart_time>}
L=${2:?usage: recover_chunk.sh <case_dir> <restart_time>}

fail() { echo "ERROR: $*" >&2; echo "RESULT: FAILED"; exit 1; }

[ -d "$dir" ] || fail "no directory $dir"
dir=$(cd "$dir" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
cd_file="$dir/system/controlDict"

[ -f "$cd_file" ]         || fail "no $cd_file"
[ -f "$dir/log.foamRun" ] || fail "no log.foamRun"
[ ! -e "$dir/log.exit" ]  || fail "log.exit exists: the chunk ended normally, use next_chunk.sh"
[[ "$L" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "restart time must be a number, got '$L'"

for pid in $(pgrep foamRun); do
    [ "$(readlink /proc/$pid/cwd 2>/dev/null)" = "$dir" ] && fail "foamRun (pid $pid) is still running in $dir"
done

[ "$(grep -cE '^startTime[[:space:]]' "$cd_file")" = 1 ] || fail "startTime not found exactly once in controlDict"
[ "$(grep -cE '^endTime[[:space:]]' "$cd_file")" = 1 ]   || fail "endTime not found exactly once in controlDict"
a=$(awk '/^startTime/ {gsub(";","",$2); print $2}' "$cd_file")
b=$(awk '/^endTime/   {gsub(";","",$2); print $2}' "$cd_file")
awk -v l="$L" -v a="$a" -v b="$b" 'BEGIN{exit !(l+0 > a+0 && l+0 < b+0)}' || fail "restart time $L must lie between startTime $a and endTime $b"

[ -d "$dir/$L" ]                                    || fail "no restart directory $dir/$L"
[ -f "$dir/$L/polyMesh/points" ]                    || fail "no moved mesh $dir/$L/polyMesh/points"
[ -f "$dir/$L/uniform/sixDoFRigidBodyMotionState" ] || fail "no body state in $dir/$L/uniform"
[ ! -e "$dir/log.foamRun.$a-$L" ]                   || fail "$dir/log.foamRun.$a-$L already exists"
[ ! -d "$dir/postProcessing/forces/$L" ]            || fail "$dir/postProcessing/forces/$L already exists"

echo "== checking restart directory and cleaning file tails in $dir"
/usr/bin/python3 -I - "$dir" "$L" <<'EOF' || fail "restart-directory check or file cleaning failed"
import glob, os, sys
d0, L = sys.argv[1], sys.argv[2]

n, bad = 0, []
for f in glob.glob(os.path.join(d0, L, "**", "*"), recursive=True):
    if os.path.isfile(f):
        n += 1
        data = open(f, "rb").read()
        if not data or b"\0" in data:
            bad.append(f)
if n == 0 or bad:
    sys.exit("restart directory %s unusable (%d files, bad: %s)" % (L, n, bad[:5]))
print("  restart directory %s: %d files, no NUL bytes, none empty" % (L, n))

targets = [d0 + "/log.foamRun"] + [f for f in glob.glob(d0 + "/postProcessing/**/*", recursive=True) if os.path.isfile(f)]
for f in targets:
    data = open(f, "rb").read()
    new = data
    notes = []
    i = data.find(b"\0")
    if i >= 0:
        if data[i:].count(b"\0") != len(data) - i:
            sys.exit("NUL bytes are not only in the tail of " + f)
        new = data[:i]
        notes.append("removed %d bytes of NUL tail" % (len(data) - i))
    if new and not new.endswith(b"\n"):
        j = new.rfind(b"\n") + 1
        if j == 0:
            sys.exit("no newline at all in " + f)
        notes.append("cut a partial last line of %d bytes" % (len(new) - j))
        new = new[:j]
    if new != data:
        open(f, "wb").write(new)
        print("  cleaned %s: %s; file now %d bytes" % (f[len(d0) + 1:], "; ".join(notes), len(new)))
EOF

mv "$dir/log.foamRun" "$dir/log.foamRun.$a-$L" || fail "could not rename log.foamRun"
sed -i -E "s/^startTime[[:space:]]+[^;]*;/startTime       $L;/" "$cd_file" || fail "sed startTime failed"
echo "== restarting from $L (interrupted chunk log kept as log.foamRun.$a-$L)"
grep -E '^(startFrom|startTime|endTime|deltaT)' "$cd_file"

bash "$here/launch_case.sh" "$dir" < /dev/null || fail "launch_case.sh failed (log already renamed, startTime already changed)"
echo "RESULT: OK"
