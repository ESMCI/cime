#!/bin/bash

DEBUG="${DEBUG:-false}"
SRC_PATH="${SRC_PATH:-`pwd`}"
# Treeless clone
GIT_FLAGS="${GIT_FLAGS:---filter=tree:0}"
# Shallow submodule checkout
GIT_SUBMODULE_FLAGS="${GIT_SUBMODULE_FLAGS:---recommend-shallow}"

echo "DEBUG = ${DEBUG}"
echo "SRC_PATH = ${SRC_PATH}"
echo "GIT_FLAGS = ${GIT_FLAGS}"
echo "GIT_SUBMODULE_FLAGS = ${GIT_SUBMODULE_FLAGS}"

if [[ "$(echo ${DEBUG} | tr -s '[:upper:]' '[:lower:]')" == "true" ]]
then
    set -x
fi

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

    [[ ! -e "${SRC_PATH}/E3SM" ]] && git clone -b ${E3SM_BRANCH:-master} ${GIT_FLAGS} ${E3SM_REPO:-https://github.com/E3SM-Project/E3SM} "${SRC_PATH}/E3SM"

    pushd "${SRC_PATH}/E3SM"

    git config --global --add safe.directory "${PWD}"

    # fix E3SM gitmodules
    fix_gitmodules "${PWD}"

    git status

    # checkout submodules
    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    # fix mct arflags flags
    fix_mct_arflags "${SRC_PATH}/E3SM/externals/mct"

    pushd cime

    # fix CIME gitmodules
    fix_gitmodules "${PWD}"

    git config --global --add safe.directory "${PWD}"
    git config --global --add safe.directory "${PWD}/CIME/non_py/cprnc"

    # checkout submodules
    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    # link v2 config_machines
    ln -sf /root/.cime/config_machines.v2.xml /root/.cime/config_machines.xml
elif [[ "${CIME_MODEL}" == "cesm" ]]
then
    echo "Setting up CESM"

    # copy pre cloned repos to new source path
    if [[ "${SRC_PATH}" != "/src/cime" ]]
    then
        cp -rf /src/ccs_config /src/components /src/libraries /src/share "${SRC_PATH}/../"
    fi

    git config --global --add safe.directory "${PWD}"
    git config --global --add safe.directory "${PWD}/CIME/non_py/cprnc"

    # fix CIME gitmodules
    fix_gitmodules "${PWD}"

    # update CIME submodules
    git submodule update --init "${GIT_SUBMODULE_FLAGS}"

    # fix mct argflags
    fix_mct_arflags /src/libraries/mct

    # link v3 config_machines
    ln -sf /root/.cime/config_machines.v3.xml /root/.cime/config_machines.xml
fi

# load batch specific entrypoint
if [[ -e "/entrypoint_batch.sh" ]]
then
    echo "Sourcing batch entrypoint"

    . "/entrypoint_batch.sh"
fi

exec "${@}"
