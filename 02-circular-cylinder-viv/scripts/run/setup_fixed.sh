#!/usr/bin/env bash
# setup_fixed.sh -- fill a fixed-cylinder case directory from cases/_template_fixed.
#
# Usage:  setup_fixed.sh <case_dir> <Re> <deltaT> <endTime> [writeInterval]
# The mesh (constant/polyMesh) must already exist: see scripts/meshing/mesh_case.sh.
# D = 1 and U = 1, so nu = 1/Re.  0/, system/ and the two constant files are overwritten.

source /opt/openfoam11/etc/bashrc
set -eo pipefail

case_dir=${1:?usage: setup_fixed.sh <case_dir> <Re> <deltaT> <endTime> [writeInterval]}
Re=${2:?}
dt=${3:?}
endt=${4:?}
wi=${5:-20}

here=$(cd "$(dirname "$0")" && pwd)
tpl="$here/../../cases/_template_fixed"

[ -d "$case_dir/constant/polyMesh" ] || { echo "ERROR: no mesh in $case_dir/constant/polyMesh" >&2; exit 1; }
[ -d "$tpl/0" ] || { echo "ERROR: template not found: $tpl" >&2; exit 1; }

rm -rf "$case_dir/0" "$case_dir/system"
cp -r "$tpl/0" "$tpl/system" "$case_dir/"
cp "$tpl/constant/physicalProperties" "$tpl/constant/momentumTransport" "$case_dir/constant/"

nu=$(/usr/bin/python3 -c "print(f'{1.0/$Re:.10g}')")
sed -i "s/^nu .*/nu              [0 2 -1 0 0 0 0] $nu;/" "$case_dir/constant/physicalProperties"
sed -i "s|^// D = 1, U = 1.*|// D = 1, U = 1  ->  Re = $Re, nu = $nu|" "$case_dir/constant/physicalProperties"

foamDictionary -entry deltaT -set "$dt" "$case_dir/system/controlDict" > /dev/null
foamDictionary -entry endTime -set "$endt" "$case_dir/system/controlDict" > /dev/null
foamDictionary -entry writeControl -set runTime "$case_dir/system/controlDict" > /dev/null
foamDictionary -entry writeInterval -set "$wi" "$case_dir/system/controlDict" > /dev/null

echo "== $case_dir"
echo "   Re $Re  nu $(foamDictionary -entry nu -value "$case_dir/constant/physicalProperties")"
for k in deltaT endTime writeControl writeInterval; do
    echo "   $k $(foamDictionary -entry $k -value "$case_dir/system/controlDict")"
done
echo "   Aref $(foamDictionary -entry forces/Aref -value "$case_dir/system/forceCoeffs")"
