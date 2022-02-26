#!/bin/bash

readonly UPDATE_CIME=${UPDATE_CIME:-"false"}

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

    git clone -b "${branch}" "${repo}" "${path}" || true
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

    local path="/src/E3SM"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${E3SM_REPO}" "${path}" "${E3SM_BRANCH:-master}"

        cd "${path}"

        if [[ ! -e "${PWD}/.gitmodules.bak" ]]
        then
            sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${PWD}/.gitmodules"
        fi

        git submodule update --init
    fi

    fixup_mct "${path}/externals/mct"

    update_cime "${path}/cime/"
}

#######################################
# Creates an environment with CESM source.
#######################################
function init_cesm() {
    export CIME_MODEL="cesm"

    local path="/src/CESM"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${CESM_REPO}" "${path}" "${CESM_BRANCH:-master}"

        cd "${path}"

        "${path}/manage_externals/checkout_externals"
    fi

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

    local path="/src/cime"

    if [[ ! -e "${path}" ]]
    then
        clone_repo "${CIME_REPO}" "${path}" "${CIME_BRANCH:-master}"

        cd "${path}"

        "/src/CESM/manage_externals/checkout_externals"
    fi

    # required to using checkout_externals script
    clone_repo "${CESM_REPO}" "/src/CESM" "${CESM_BRANCH:-master}"

    mamba install -c conda-forge -y pytest pytest-cov 

    fixup_mct "${path}/libraries/mct"
}

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
