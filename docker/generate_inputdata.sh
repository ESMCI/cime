#!/bin/bash
set -Eeuo pipefail

# Generates the input data bundle baked into docker/Dockerfile.data, then
# builds and pushes that image (see docker/README.md's "Input data image"
# section). Runs natively on the host -- no container needed. CIME's core
# scripts (create_newcase, case.setup, check_input_data) have zero Python
# dependencies (see setup.py), and only need a config_machines.xml
# defining the "docker" machine (normally supplied by the CI image's
# /root/.cime) plus the svn/wget/git CLIs that a real download needs.
# svn is provisioned via a small local pixi env (docker/inputdata-env/)
# since it's the one tool least likely to already be installed; wget and
# git are assumed present.
#
# This must be run from a network that can actually reach the input data
# servers (NERSC's portal, LCRC, the CGD SVN mirror) -- notably NOT a
# GitHub Actions runner, which cannot reach portal.nersc.gov (see
# docker/README.md).
#
# Usage (from this repo's checkout, which must be the "cime" submodule of
# a full E3SM checkout):
#
#   ./docker/generate_inputdata.sh              # generate, build, push
#   ./docker/generate_inputdata.sh --skip-push  # generate only
#
# Populates docker/inputdata/ (default; override with OUT_DIR) with every
# file needed to:
#   - run the cime_developer test suite (CIME.get_tests._CIME_TESTS),
#     across every unique grid/compset pair it uses
#   - run tools/mapping/gen_domain_files/test_gen_domain.sh
#
# Unit tests (CIME/tests/test_unit_*.py) are not included: they mock all
# network/server access and do not read real input data.
#
# The pushed tag comes from INPUTDATA_VERSION, not "latest": CI reads that
# same file to know which tag to pull, so bump it in the same PR as any
# change to the data (e.g. cime_developer's test list changing), keeping
# the reference CI uses explicit and reviewable instead of a mutable tag
# that could silently go stale.

SKIP_PUSH=0
[[ "${1:-}" == "--skip-push" ]] && SKIP_PUSH=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CIME_ROOT="${CIME_ROOT:-${SCRIPT_DIR}/..}"
OUT_DIR="${OUT_DIR:-${SCRIPT_DIR}/inputdata}"
CASES_DIR="${CASES_DIR:-$(mktemp -d)}"

mkdir -p "$OUT_DIR" "$CASES_DIR"

# svn is the one tool here unlikely to already be on PATH; provision it
# via a small local pixi env rather than requiring root/apt.
if ! command -v svn >/dev/null 2>&1; then
    echo "svn not found on PATH; installing via docker/inputdata-env (pixi)..."
    (cd "${SCRIPT_DIR}/inputdata-env" && pixi install --frozen)
    export PATH="${SCRIPT_DIR}/inputdata-env/.pixi/envs/default/bin:${PATH}"
fi
for tool in svn wget git python3 docker; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "ERROR: required tool '$tool' not found on PATH." >&2
        exit 1
    }
done

# config_machines.xml defining the "docker" machine used by all of these
# cases; normally supplied by the CI image's /root/.cime, not present in
# a bare E3SM checkout.
MACHINES_DIR="$(mktemp -d)"
cp "${SCRIPT_DIR}/.cime/config_machines.v2.xml" "${MACHINES_DIR}/config_machines.xml"

# Env vars config_machines.xml's "docker" entry expects, normally set by
# docker/entrypoint.sh's activate_pixi_env()/compute_container_cores().
# LD_LIBRARY_PATH/PKG_CONFIG_PATH only need to be *defined* (referenced
# via $ENV{...}), not point anywhere meaningful, since we're not
# compiling/linking anything here -- these are all data-only compsets.
export DOCKER_MAX_TASKS="${DOCKER_MAX_TASKS:-$(nproc)}"
export CIME_MODEL="${CIME_MODEL:-e3sm}"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
export PKG_CONFIG_PATH="${PKG_CONFIG_PATH:-}"

git config --global user.name "data-gen" 2>/dev/null || true
git config --global user.email "data-gen@example.com" 2>/dev/null || true
git config --global --add safe.directory "*" 2>/dev/null || true

# Derive the unique (grid, compset) pairs actually used by cime_developer,
# so this script tracks that test list automatically instead of duplicating
# it here.
pairs="$(
    cd "$CIME_ROOT" && python3 -c "
from CIME.get_tests import _CIME_TESTS
pairs = sorted({(t.split('.')[1], t.split('.')[2]) for t in _CIME_TESTS['cime_developer']['tests']})
for grid, compset in pairs:
    print('{}|{}'.format(grid, compset))
"
)"

cd "$CIME_ROOT/scripts"

while IFS='|' read -r grid compset; do
    casename="${CASES_DIR}/${grid}_${compset}"
    echo "=== Creating case: grid=${grid} compset=${compset} ==="
    rm -rf "$casename"
    python3 ./create_newcase --case "$casename" --res "$grid" --compset "$compset" \
        --machine docker --extra-machines-dir "$MACHINES_DIR" -i "$OUT_DIR"

    pushd "$casename" >/dev/null
    python3 ./case.setup
    echo "--- Downloading input data for ${grid}/${compset} ---"
    python3 ./check_input_data --download
    popd >/dev/null
done <<< "$pairs"

echo "=== Downloading gen_domain grid data ==="
mkdir -p "$OUT_DIR/cpl/gridmaps/oQU240" "$OUT_DIR/share/domains"
gen_domain_files=(
    "cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc"
    "share/domains/domain.ocn.ne4np4_oQU240.160614.nc"
    "share/domains/domain.lnd.ne4np4_oQU240.160614.nc"
)
for f in "${gen_domain_files[@]}"; do
    dest="$OUT_DIR/$f"
    [[ -s "$dest" ]] && continue
    wget -q -O "$dest" "https://portal.nersc.gov/project/e3sm/inputdata/$f"
done

rm -rf "$MACHINES_DIR"

echo "=== Generated ==="
du -sh "$OUT_DIR"
find "$OUT_DIR" -type f | wc -l

if [[ "$SKIP_PUSH" -eq 1 ]]; then
    echo "--skip-push given; not building/pushing an image."
    exit 0
fi

VERSION="$(<"${SCRIPT_DIR}/INPUTDATA_VERSION")"
IMAGE="ghcr.io/esmci/cime-inputdata:v${VERSION}"

echo "=== Building ${IMAGE} ==="
docker build -f "${SCRIPT_DIR}/Dockerfile.data" -t "$IMAGE" "$SCRIPT_DIR"

echo "=== Pushing ${IMAGE} ==="
docker push "$IMAGE"

echo "Done: ${IMAGE}"
