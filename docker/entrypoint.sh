#!/bin/bash

export USER=root
export LOGNAME=root
export USER_ID=${USER_ID:-1000}
export GROUP_ID=${GROUP_ID:-1000}

SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"

function fix_mct_makefiles() {
    fix_arflags "${1}/mct/Makefile"
    fix_arflags "${1}/mpeu/Makefile"
    fix_arflags "${1}/mpi-serial/Makefile"
}

function fix_arflags() {
    if [[ ! -e "${1}.bak" ]]; then
        echo "Fixing AR variable in ${1}"

        sed -i".bak" "s/\$(AR)/\$(AR) \$(ARFLAGS)/g" "${1}"
    fi
}

function build_cprnc() {
    cprnc_dir="${SRC_PATH:-`pwd`}/CIME/non_py/cprnc"

    pushd `mktemp -d`

    cmake "${cprnc_dir}"

    make

    cp cprnc /home/cime/tools/cprnc

    popd
}

function download_input_data() {
    mkdir -p /home/cime/inputdata/cpl/gridmaps/oQU240 \
        /home/cime/inputdata/share/domains \
        /home/cime/timings \
        /home/cime/cases \
        /home/cime/archive \
        /home/cime/baselines \
        /home/cime/tools

    wget -O /home/cime/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc

    wget -O /home/cime/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc

    wget -O /home/cime/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}

function link_config_machines() {
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf ${1}/.cime/config_machines.v2.xml ${1}/.cime/config_machines.xml
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        export ESMFMKFILE=/opt/conda/envs/cesm/lib/esmf.mk

        ln -sf ${1}/.cime/config_machines.v3.xml ${1}/.cime/config_machines.xml
    fi
}

user_home=/home/cime

if [[ "${USER_ID}" == "0" ]]; then
    user_home=/root

    cp -rf /home/cime/.cime /root/
fi

{
    echo "source /opt/conda/etc/profile.d/conda.sh"
    echo "conda activate base"
    echo "if [[ ${CIME_MODEL} == 'e3sm' ]]; then"
    echo "  conda activate e3sm"
    echo "elif [[ ${CIME_MODEL} == 'cesm' ]]; then"
    echo "  conda activate cesm"
    echo "fi"
    # need this to perfer host perl over conda
    echo "export PATH=/usr/bin:\$PATH"
} > ${user_home}/.bashrc

link_config_machines ${user_home}

if [[ -e "${PWD}/.git" ]]; then
    git config --global --add safe.directory "*"
elif [[ -n "${SRC_PATH}" ]]; then
    pushd "${SRC_PATH}"
    git config --global --add safe.directory "*"
    popd
fi

if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    if [[ "${USER_ID}" == "0" ]]; then
        exec "${@}"
    else
        groupmod -g "${GROUP_ID}" -n cime ubuntu
        usermod -d /home/cime -u "${USER_ID}" -g "${GROUP_ID}" -l cime ubuntu

        chown -R cime:cime /home/cime
        chmod -R 775 /home/cime

        if [[ -n "${SRC_PATH}" ]] && [[ -e "${SRC_PATH}" ]]; then
            chown -R cime:cime "${SRC_PATH}"
            chmod -R 775 "${SRC_PATH}"
        fi

        gosu "${USER_ID}" "${@}"
    fi
fi
