#!/bin/bash

DEBUG="${DEBUG:-false}"
SRC_PATH="${SRC_PATH:-`pwd`}"
# Treeless clone
GIT_FLAGS="${GIT_FLAGS:---filter=tree:0}"
# Shallow submodule checkout
GIT_SUBMODULE_FLAGS="${GIT_SUBMODULE_FLAGS:---recommend-shallow}"
SKIP_MODEL_SETUP="${SKIP_MODEL_SETUP:-false}"
CIME_REMOTE="${CIME_REMOTE:-https://github.com/ESMCI/cime}"
CIME_BRANCH="${CIME_BRANCH:-master}"
SKIP_CIME_UPDATE="${SKIP_CIME_UPDATE:-false}"

echo "DEBUG = ${DEBUG}"
echo "SRC_PATH = ${SRC_PATH}"
echo "GIT_FLAGS = ${GIT_FLAGS}"
echo "GIT_SUBMODULE_FLAGS = ${GIT_SUBMODULE_FLAGS}"
echo "SKIP_MODEL_SETUP = ${SKIP_MODEL_SETUP}"
echo "CIME_REMOTE = ${CIME_REMOTE}"
echo "CIME_BRANCH = ${CIME_BRANCH}"
echo "SKIP_CIME_UDPATE = ${SKIP_CIME_UPDATE}"

function to_lowercase() {
    echo "${!1}" | tr -s '[:upper:]' '[:lower:]'
}

if [[ "$(to_lowercase DEBUG)" == "true" ]]; then
    set -x
fi

#######################################
# Fixes mct/mpeu to use ARFLAGS environment variable
#
# TODO need to make an offical PR this is temporary.
#######################################
function fix_mct_arflags() {
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

if [[ "${SKIP_MODEL_SETUP}" == "false" ]]; then
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        echo "Setting up E3SM"

        [[ ! -e "${SRC_PATH}/E3SM" ]] && git clone -b ${E3SM_BRANCH:-master} ${GIT_FLAGS} ${E3SM_REPO:-https://github.com/E3SM-Project/E3SM} "${SRC_PATH}/E3SM"

        pushd "${SRC_PATH}/E3SM"

        git config --global --add safe.directory "*"

        # fix E3SM gitmodules
        fix_gitmodules "${PWD}"

        # checkout submodules
        git submodule update --init "${GIT_SUBMODULE_FLAGS}"

        # fix mct arflags flags
        fix_mct_arflags "${SRC_PATH}/E3SM/externals/mct"

        git status
        git submodule status

        pushd cime
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        echo "Setting up CESM"

        [[ ! -e "${SRC_PATH}/CESM" ]] && git clone -b ${CESM_BRANCH:-master} ${GIT_FLAGS} ${E3SM_REPO:-https://github.com/ESCOMP/CESM} "${SRC_PATH}/CESM"

        pushd "${SRC_PATH}/CESM"

        git config --global --add safe.directory "*"

        ./bin/git-fleximod update

        git status
        git submodule status

        pushd cime
    fi
fi

git config --global --add safe.directory "`pwd`"

if [[ "$(to_lowercase SKIP_CIME_UPDATE)" == "false" ]]; then
    fix_gitmodules "${PWD}"

    # Expect current directory to be CIME
    git remote set-url origin "${CIME_REMOTE}"
    git remote set-branches origin "*"
    git fetch origin
    git checkout "${CIME_BRANCH}"

    # Sync submodules
    git submodule update --init
fi

git status
git submodule status

if [[ "${CIME_MODEL}" == "e3sm" ]]; then
    # link v2 config_machines
    ln -sf /root/.cime/config_machines.v2.xml /root/.cime/config_machines.xml
elif [[ "${CIME_MODEL}" == "cesm" ]]; then
    # link v3 config_machines
    ln -sf /root/.cime/config_machines.v3.xml /root/.cime/config_machines.xml
fi

# load batch specific entrypoint
if [[ -e "/entrypoint_batch.sh" ]]
then
    echo "Sourcing batch entrypoint"

    . "/entrypoint_batch.sh"
fi

function create_environment() {
    mamba create -n cime-$1 python=$1
    mamba env update -n cime-$1 -f /cime.yaml

    source /opt/conda/etc/profile.d/conda.sh

    conda activate cime-$1
}

exec "${@}"
