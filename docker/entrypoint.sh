#!/bin/bash

if [[ -n "${DEBUG}" ]]
then
    set -x
fi

SRC_PATH="`pwd`"
GIT_FLAGS="--filter=tree:0"
GIT_SUBMODULE_FLAGS="--recommend-shallow"

#######################################
# Fixes mct/mpeu to use ARFLAGS environment variable
#
# TODO need to make an offical PR this is temporary.
#######################################
function fix_mct_arflags {
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
# Fixes gitmodules to use https rather than ssh
#######################################
function fix_gitmodules() {
    sed -i".bak" "s/git@github.com:/https:\/\/github.com\//g" "${1}/.gitmodules"
}

if [[ "${CIME_MODEL}" == "e3sm" ]]
then
    echo "Setting up E3SM"

    git clone -b ${E3SM_BRANCH:-master} ${GIT_FLAGS} ${E3SM_REPO:-https://github.com/E3SM-Project/E3SM} "${SRC_PATH}/E3SM"

    pushd "${SRC_PATH}/E3SM"

    fix_gitmodules "${PWD}"

    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    fix_mct_arflags "${SRC_PATH}/E3SM/externals/mct"

    pushd cime

    fix_gitmodules "${PWD}"

    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    ln -sf /root/.cime/config_machines.v2.xml /root/.cime/config_machines.xml
elif [[ "${CIME_MODEL}" == "cesm" ]]
then
    echo "Setting up CESM"

    if [[ "${SRC_PATH}" != "/src" ]]
    then
        cp -rf /src/ccs_config /src/components /src/libraries /src/share ../
    fi

    git config --global --add safe.directory "${PWD}"

    fix_gitmodules "${PWD}"

    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    git config --global --add safe.directory "${PWD}/cime"

    fix_mct_arflags /src/libraries/mct

    ln -sf /root/.cime/config_machines.v3.xml /root/.cime/config_machines.xml
fi

# load batch specific entrypoint
if [[ -e "/entrypoint_batch.sh" ]]
then
    echo "Sourcing batch entrypoint"

    . "/entrypoint_batch.sh"
fi

exec "${@}"
