#!/bin/bash

# Set up basic user, logname, and default group/user IDs
export USER="$(id -nu)"
export LOGNAME="${USER}"
export USER_ID="${USER_ID:-1000}"
export GROUP_ID="${GROUP_ID:-1000}"

# Set static home path where .cime exists and container entrypoint options
CIME_HOME="/home/cime"
SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"
SRC_PATH="${SRC_PATH:-${PWD}}"


# Determine HOME directory: use provided HOME in CI, /root if root, default otherwise
if [[ "${USER_ID}" == "0" ]]; then
    HOME="/root"
elif [[ "${CI:-false}" == "false" ]]; then
    # Not populated in $HOME until gosu switches user
    HOME="/home/cime"
fi


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

    pushd `mktemp -d`

    cmake "${cprnc_dir}"

    make

    # Needs to be copied into the machines configured tool path
    cp cprnc "${CIME_HOME}/tools/cprnc"

    popd
}


# Download input data needed for model setup
function download_input_data() {
    mkdir -p "${CIME_HOME}/inputdata/cpl/gridmaps/oQU240" \
        "${CIME_HOME}/inputdata/share/domains" \
        "${CIME_HOME}/timings" \
        "${CIME_HOME}/cases" \
        "${CIME_HOME}/archive" \
        "${CIME_HOME}/baselines" \
        "${CIME_HOME}/tools"

    wget -O "${CIME_HOME}/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc

    wget -O "${CIME_HOME}/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc

    wget -O "${CIME_HOME}/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc" \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}


# Link correct config_machines file based on CIME_MODEL, also set ESMFMKFILE for cesm
function link_config_machines() {
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf "${CIME_HOME}/.cime/config_machines.v2.xml" "${HOME}/.cime/config_machines.xml"
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        export ESMFMKFILE=/opt/conda/envs/cesm/lib/esmf.mk

        ln -sf "${CIME_HOME}/.cime/config_machines.v3.xml" "${HOME}/.cime/config_machines.xml"
    fi
}


# If root or in CI, move .cime config to the appropriate home directory
if [[ "${USER_ID}" == "0" ]] || [[ "${CI:-false}" == "true" ]]; then
    cp -rf "${CIME_HOME}/.cime" "${HOME}"
fi


# Write minimal .bashrc to activate correct conda environment and ensure system perl is preferred
{
    echo "source /opt/conda/etc/profile.d/conda.sh"
    echo "conda activate base"
    echo "if [[ ${CIME_MODEL} == 'e3sm' ]]; then"
    echo "  conda activate e3sm"
    echo "elif [[ ${CIME_MODEL} == 'cesm' ]]; then"
    echo "  conda activate cesm"
    echo "fi"
    # Clobber PATH so system perl is used instead of conda perl
    echo "export PATH=/usr/bin:\$PATH"
} > "${HOME}/.bashrc"


link_config_machines

# Allow git to operate in any directory, for container/dev scenarios
if [[ -e "${SRC_PATH}/.git" ]]; then
    git config --global --add safe.directory "*"
fi


# If not skipping entrypoint, set up user/group IDs and exec given command.
if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    if [[ "${USER_ID}" == "0" ]]; then
        exec "${@}"
    else
        # Modify user/group, useful for local in-container development
        groupmod -g "${GROUP_ID}" -n cime ubuntu
        usermod -d "${HOME}" -u "${USER_ID}" -g "${GROUP_ID}" -l cime ubuntu

        chown -R cime:cime "${HOME}"

        gosu "${USER_ID}" "${@}"
    fi
fi
