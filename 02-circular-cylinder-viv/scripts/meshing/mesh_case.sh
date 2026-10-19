#!/usr/bin/env bash
# mesh_case.sh -- build the OpenFOAM mesh of a fixed-cylinder case from one resolution level.
#
# Usage:  mesh_case.sh <coarse|medium|fine> <case_dir>
# Steps:  Gmsh (cylinder_mesh.py) -> gmshToFoam -> patch types -> checkMesh summary.
# The .msh file goes to $MESH_DIR (default ~/work_scratch/p02/meshes), not into the repository.
#
# Optional environment variables:
#   MESH_DIR   directory for the .msh file
#   MESH_TAG   tag added to the .msh file name (cyl_<level>_<tag>.msh), e.g. y30
#   MESH_ARGS  extra arguments for cylinder_mesh.py, e.g. "--y-half 30"
#   FORCE=1    allow overwriting an existing .msh file (refused by default)

# OpenFOAM's bashrc is not safe under 'set -u', so source it first.
source /opt/openfoam11/etc/bashrc
set -eo pipefail

level=${1:?usage: mesh_case.sh <coarse|medium|fine> <case_dir>}
case_dir=${2:?usage: mesh_case.sh <coarse|medium|fine> <case_dir>}
here=$(cd "$(dirname "$0")" && pwd)
mesh_dir=${MESH_DIR:-$HOME/work_scratch/p02/meshes}
mesh="$mesh_dir/cyl_${level}${MESH_TAG:+_$MESH_TAG}.msh"

mkdir -p "$mesh_dir" "$case_dir/system" "$case_dir/constant"

# Gmsh output is not bit-identical between runs: never replace a mesh that cases already use.
if [ -e "$mesh" ] && [ -z "${FORCE:-}" ]; then
    echo "refusing to overwrite existing mesh $mesh (set FORCE=1 to allow)" >&2
    exit 1
fi

# placeholder controlDict, only so gmshToFoam / checkMesh can run; never overwrites an existing one
if [ ! -f "$case_dir/system/controlDict" ]; then
cat > "$case_dir/system/controlDict" <<'EOF'
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}

application     foamRun;
solver          incompressibleFluid;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1;
deltaT          0.001;

writeControl    timeStep;
writeInterval   100;
EOF
fi

# ${MESH_ARGS:-} is deliberately unquoted so that it splits into separate arguments
/usr/bin/python3 "$here/cylinder_mesh.py" --level "$level" ${MESH_ARGS:-} --out "$mesh" > "$case_dir/log.gmsh" 2>&1
md5sum "$mesh" > "$case_dir/mesh.md5"   # Gmsh output differs slightly between runs; record the one used
echo "level=$level tag=${MESH_TAG:-} args=${MESH_ARGS:-}" > "$case_dir/mesh.args"

rm -rf "$case_dir/constant/polyMesh"
gmshToFoam -case "$case_dir" "$mesh" > "$case_dir/log.gmshToFoam" 2>&1

b="$case_dir/constant/polyMesh/boundary"
sed -i -e '/^    back$/,/}/ s/^        type            patch;/        type            empty;/' \
       -e '/^    front$/,/}/ s/^        type            patch;/        type            empty;/' \
       -e '/^    cylinder$/,/}/ s/^        type            patch;/        type            wall;/' \
       -e '/physicalType/d' "$b"

checkMesh -case "$case_dir" -allGeometry -allTopology > "$case_dir/log.checkMesh" 2>&1 || true

echo "== $level ($case_dir)"
grep -E 'cells:|hexahedra|prisms|polyhedra|solution|Max aspect|non-orthogonality Max|Max skewness|Total volume|Mesh OK|Failed|\*\*\*' "$case_dir/log.checkMesh"
