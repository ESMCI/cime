#!/bin/bash

# Set up basic user, logname, and default group/user IDs
export USER="$(id -nu)"
export LOGNAME="${USER}"
export USER_ID="${USER_ID:-1000}"
export GROUP_ID="${GROUP_ID:-1000}"

# Set static home path where .cime exists and container entrypoint options
SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"

# Fix AR variable in MCT-related Makefiles
function fix_mct_makefiles() {
    fix_arflags "${1}/mct/Makefile"
    fix_arflags "${1}/mpeu/Makefile"
    fix_arflags "${1}/mpi-serial/Makefile"
}


# Add ARFLAGS to AR in a Makefile if .bak does not exist
function fix_arflags() {
    if [[ ! -e "${1}.bak" ]]; then
        echo "Fixing AR variable in ${1}"

        sed -i".bak" "s/\$(AR)/\$(AR) \$(ARFLAGS)/g" "${1}"
    fi
}


# Build the cprnc tool from CIME sources
function build_cprnc() {
    cprnc_dir="${PWD}/CIME/non_py/cprnc"

    if [[ ! -e "${cprnc_dir}" ]]; then
        echo "CPRNC path does not exist. Change to CIME's root directory."
        exit 1
    fi

    pushd "$(mktemp -d)" || exit 1

    cmake "${cprnc_dir}"

    make

    # Needs to be copied into the machines configured tool path
    cp cprnc "${HOME}/tools/cprnc"

    popd || exit 1
}


# Download input data needed for model setup
function download_input_data() {
    mkdir -p "${HOME}/inputdata/cpl/gridmaps/oQU240" \
        "${HOME}/inputdata/share/domains" \
        "${HOME}/timings" \
        "${HOME}/cases" \
        "${HOME}/archive" \
        "${HOME}/baselines" \
        "${HOME}/tools"

    wget -O "${HOME}/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc

    wget -O "${HOME}/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc

    wget -O "${HOME}/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}


# Link correct config_machines file based on CIME_MODEL, also set ESMFMKFILE for cesm
function link_config_machines() {
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf "${HOME}/.cime/config_machines.v2.xml" "${HOME}/.cime/config_machines.xml"
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        export ESMFMKFILE=/opt/conda/envs/cesm/lib/esmf.mk

        ln -sf "${HOME}/.cime/config_machines.v3.xml" "${HOME}/.cime/config_machines.xml"
    fi
}

if [[ "${CI:-false}" == "true" ]]; then
  cp -rf /root/.cime "${HOME}"
fi

link_config_machines

# Allow git to operate in any directory, for container/dev scenarios
if [[ -e "${PWD}/.git" ]]; then
    git config --global --add safe.directory "*"
fi

export PATH=/opt/spack-envs/view/bin:$PATH
export PKG_CONFIG_PATH=/opt/spakc-envs/view/pkgconfig
export LD_LIBRARY_PATH=/opt/spack-envs/view/lib

if [[ "${CI:-false}" == "true" ]]; then
  source ${HOME}/.local/bin/env
  source ${HOME}/.venv/bin/activate
fi

# If not skipping entrypoint, set up user/group IDs and exec given command.
if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    exec "${@}"
fi
