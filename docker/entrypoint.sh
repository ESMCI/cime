#!/bin/bash

if [[ -n "${DEBUG}" ]]
then
    set -x
fi

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
        extras="${extras} --depth 1"
    fi

    echo "Cloning branch ${branch} of ${repo} into ${path} with flags: ${flags}"

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
        echo "Fixing AR variable in ${mct_path}/mct/Makefile"

        sed -i".bak" "s/\$(AR)/\$(AR) \$(ARFLAGS)/g" "${mct_path}/mct/Makefile"
    fi

    if [[ ! -e "${mct_path}/mpeu/Makefile.bak" ]]
    then
        echo "Fixing AR variable in ${mct_path}/mpeu/Makefile"

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
    echo "Setting up E3SM"

    export CIME_MODEL="e3sm"

    local extras=""
    local install_path="${INSTALL_PATH:-/src/E3SM}"
    local cache_path="${cache_path:-/storage/inputdata}"

    if [[ ! -e "${install_path}" ]]
    then
        clone_repo "${E3SM_REPO}" "${install_path}" "${E3SM_BRANCH:-master}"

        cd "${install_path}"

        if [[ ! -e "${PWD}/.gitmodules.bak" ]]
        then
            echo "Convering git@github.com to https://github.com urls in ${PWD}/.gitmodules"

            sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
        fi

        if [[ "${GIT_SHALLOW}" == "true" ]]
        then
            extras=" --depth 1"
        fi

        echo "Initializing submodules in ${PWD}"

        git submodule update --init ${extras}
    fi

    fixup_mct "${install_path}/externals/mct"

    update_cime "${install_path}/cime"

    mkdir -p /storage/inputdata

    echo "Copying cached inputdata from /cache to /storage/inputdata"

    rsync -vr /cache/ /storage/inputdata/

    cd "${install_path}/cime"

    if [[ ! -e "${PWD}/.gitmodules.bak" ]]
    then
        echo "Convering git@github.com to https://github.com urls in ${PWD}/.gitmodules"

        sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
    fi

    echo "Initializing submodules in ${PWD}"

    git submodule update --init ${extras}
}

#######################################
# Creates an environment with CESM source.
#######################################
function init_cesm() {
    echo "Setting up CESM"

    export CIME_MODEL="cesm"

    local install_path="${INSTALL_PATH:-/src/CESM}"

    if [[ ! -e "${install_path}" ]]
    then
        clone_repo "${CESM_REPO}" "${install_path}" "${CESM_BRANCH:-master}"
    fi

    pushd "${install_path}"

    pushd "${install_path}/cime"

    echo "Checking out externals from `pwd`"

    "${install_path}/manage_externals/checkout_externals" -v

    popd

    fixup_mct "${install_path}/libraries/mct"

    update_cime "${install_path}/cime/"

    pushd "${install_path}/cime"

    # Need to run manage_externals again incase branch changes externals instructions
    # "${install_path}/manage_externals/checkout_externals -e cime/Externals_cime.cfg"

    if [[ ! -e "${PWD}/.gitmodules.bak" ]]
    then
        echo "Convering git@github.com to https://github.com urls in ${PWD}/.gitmodules"

        sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
    fi

    git submodule update --init
}

#######################################
# Creates an environment with minimal model requirements.
# Similar to old github actions environment.
#######################################
function init_cime() {
    echo "Settig up CIME"

    export CIME_MODEL="cesm"
    export ESMFMKFILE="/opt/conda/lib/esmf.mk"

    local install_path="${INSTALL_PATH:-/src/cime}"

    if [[ ! -e "${install_path}" ]]
    then
        clone_repo "${CIME_REPO}" "${install_path}" "${CIME_BRANCH:-master}"
    fi

    # required to using checkout_externals script
    clone_repo "${CESM_REPO}" "/src/CESM" "${CESM_BRANCH:-master}"

    cd "${install_path}"

    "/src/CESM/manage_externals/checkout_externals" -v

    fixup_mct "${install_path}/libraries/mct"

    update_cime "${install_path}"

    cd "${install_path}"

    # Need to run manage_externals again incase branch changes externals instructions
    # "${install_path}/manage_externals/checkout_externals -e cime/Externals_cime.cfg"

    if [[ ! -e "${PWD}/.gitmodules.bak" ]]
    then
        echo "Convering git@github.com to https://github.com urls in ${PWD}/.gitmodules"

        sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
    fi

    git submodule update --init
}

if [[ ! -e "${HOME}/.cime" ]]
then
    ln -sf "/root/.cime" "${HOME}/.cime"
fi

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
