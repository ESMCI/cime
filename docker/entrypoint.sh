#!/bin/bash

set -x

readonly INIT=${INIT:-"true"}
readonly UPDATE_CIME=${UPDATE_CIME:-"false"}
readonly GIT_SHALLOW=${GIT_SHALLOW:-"false"}

declare -xr CIME_REPO=${CIME_REPO:-https://github.com/ESMCI/cime}
declare -xr E3SM_REPO=${E3SM_REPO:-https://github.com/E3SM-Project/E3SM}
declare -xr CESM_REPO=${CESM_REPO:-https://github.com/ESCOMP/CESM}

#######################################
# Clones git repository
#######################################
function clone_repo() {
    local repo="${1}"
    local path="${2}"
    local branch="${3}"
    local extras=""

    if [[ "${GIT_SHALLOW}" == "true" ]]
    then
        extras=" --depth 1"
    fi

    git clone -b "${branch}" ${extras} "${repo}" "${path}" || true
}

#######################################
# Fixes mct/mpeu to use ARFLAGS environment variable
#
# TODO need to make an offical PR this is temporary.
#######################################
function fixup_mct {
    local mct_path="${1}"

    # TODO make PR to fix
    if [[ ! -e "${mct_path}/mct/Makefile.bak" ]]
    then
        sed -i".bak" "s/\$(AR)/\$(AR) \$(ARFLAGS)/g" "${mct_path}/mct/Makefile"
    fi

    if [[ ! -e "${mct_path}/mpeu/Makefile.bak" ]]
    then
        sed -i".bak" "s/\$(AR)/\$(AR) \$(ARFLAGS)/g" "${mct_path}/mpeu/Makefile"
    fi
}

#######################################
#######################################
function update_cime() {
    local path="${1}"

    if [[ "${UPDATE_CIME}" == "true" ]]
    then
        echo "Updating CIME using repository ${CIME_REPO} and branch ${CIME_BRANCH}"

        pushd "${path}"

        git remote set-url origin "${CIME_REPO}"

        if [[ "${GIT_SHALLOW}" == "true" ]]
        then
            git remote set-branches origin "*"
        fi

        git fetch origin

        git checkout "${CIME_BRANCH:-master}"

        popd
    fi
}

#######################################
# Creates an environment with E3SM source.
#######################################
function init_e3sm() {
    export CIME_MODEL="e3sm"
    export LOGNAME="test.log"

    local extras=""
    local path="${INSTALL_PATH:-/src/E3SM}"
    local cache_path="${CACHE_PATH:-/storage/inputdata}"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${E3SM_REPO}" "${path}" "${E3SM_BRANCH:-master}"

        cd "${path}"

        if [[ ! -e "${PWD}/.gitmodules.bak" ]]
        then
            sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
        fi

        if [[ "${GIT_SHALLOW}" == "true" ]]
        then
            extras=" --depth 1"
        fi

        git submodule update --init ${extras}
    fi

    fixup_mct "${path}/externals/mct"

    update_cime "${path}/cime/"

    curl -L --create-dirs \
        -o ${cache_path}/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc \
        https://web.lcrc.anl.gov/public/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc
    curl -L --create-dirs \
        -o ${cache_path}/share/domains/domain.ocn.ne4np4_oQU240.160614.nc \
        https://web.lcrc.anl.gov/public/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc
    curl -L --create-dirs \
        -o ${cache_path}/share/domains/domain.lnd.ne4np4_oQU240.160614.nc \
        https://web.lcrc.anl.gov/public/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}

#######################################
# Creates an environment with CESM source.
#######################################
function init_cesm() {
    export CIME_MODEL="cesm"

    local path="${INSTALL_PATH:-/src/CESM}"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${CESM_REPO}" "${path}" "${CESM_BRANCH:-master}"
    fi

    cd "${path}"

    "${path}/manage_externals/checkout_externals"

    fixup_mct "${path}/libraries/mct"

    update_cime "${path}/cime/"
}

#######################################
# Creates an environment with minimal model requirements.
# Similar to old github actions environment.
#######################################
function init_cime() {
    export CIME_MODEL="cesm"
    export ESMFMKFILE="/opt/conda/lib/esmf.mk"

    local path="${INSTALL_PATH:-/src/cime}"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${CIME_REPO}" "${path}" "${CIME_BRANCH:-master}"
    fi

    # required to using checkout_externals script
    clone_repo "${CESM_REPO}" "/src/CESM" "${CESM_BRANCH:-master}"

    cd "${path}"

    "/src/CESM/manage_externals/checkout_externals"

    fixup_mct "${path}/libraries/mct"

    update_cime "${path}"
}

if [[ -e "/entrypoint_batch.sh" ]]
then
    echo "Sourcing batch entrypoint"

    . "/entrypoint_batch.sh"
fi

if [[ "${INIT}" == "true" ]]
then
    if [[ "${CIME_MODEL}" == "e3sm" ]]
    then
        init_e3sm
    elif [[ "${CIME_MODEL}" == "cesm" ]]
    then
        init_cesm
    else
        init_cime
    fi

    exec "${@}"
fi