#!/bin/bash

# Set up basic user, logname, and default group/user IDs
export USER="$(id -nu)"
export LOGNAME="${USER}"

# Set static home path where .cime exists and container entrypoint options
SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"
STORAGE_DIR="${HOME}/storage"

# Build the cprnc tool from CIME sources
function build_cprnc() {
    cprnc_dir="${CPRNC_DIR:-${PWD}/CIME/non_py/cprnc}"
    tools_dir="${STORAGE_DIR}/tools"

    if [[ ! -e "${cprnc_dir}" ]]; then
        echo "CPRNC path does not exist. Change to CIME's root directory."
        exit 1
    fi

    pushd "$(mktemp -d)" || exit 1

    cmake -S "${cprnc_dir}" -B .

    make

    [[ ! -e "${tools_dir}" ]] && mkdir -p "${tools_dir}"

    # Needs to be copied into the machines configured tool path
    cp cprnc "${tools_dir}/cprnc"

    popd || exit 1
}


# Download input data needed for model setup
# required for grid generation tests
function download_input_data() {
    mkdir -p "${STORAGE_DIR}/inputdata/cpl/gridmaps/oQU240"
    mkdir -p "${STORAGE_DIR}/inputdata/share/domains"

    wget -O "${STORAGE_DIR}/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc

    wget -O "${STORAGE_DIR}/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc

    wget -O "${STORAGE_DIR}/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}


# Link correct config_machines file based on CIME_MODEL, also set ESMFMKFILE for cesm
function link_config_machines() {
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf "${HOME}/.cime/config_machines.v2.xml" "${HOME}/.cime/config_machines.xml"
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        ln -sf "${HOME}/.cime/config_machines.v3.xml" "${HOME}/.cime/config_machines.xml"
    fi
}

export PATH=/opt/spack-envs/view/bin:$PATH
export PKG_CONFIG_PATH=/opt/spack-envs/view/lib/pkgconfig
export LD_LIBRARY_PATH=/opt/spack-envs/view/lib
export ESMFMKFILE=/opt/spack-envs/view/lib/esmf.mk

if [[ "${CI:-false}" == "true" ]]; then
  cp -rf /root/.cime "${HOME}"
fi

link_config_machines

# Allow git to operate in any directory, for container/dev scenarios
if [[ -e "${PWD}/.git" ]]; then
    git config --global --add safe.directory "*"
fi

if [[ "${CI:-false}" == "false" ]] && [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
  source ${HOME}/.local/bin/env
  source ${HOME}/.venv/bin/activate
fi

if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    exec "${@}"
fi
