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

if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf /home/cime/.cime/config_machines.v2.xml /home/cime/.cime/config_machines.xml
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        export ESMFMKFILE=/opt/conda/envs/cesm/lib/esmf.mk

        ln -sf /home/cime/.cime/config_machines.v3.xml /home/cime/.cime/config_machines.xml
    fi

    if [[ "${USER_ID}" == "0" ]]; then
        cp -rf /home/cime/.cime /root/

        git config --global --add safe.directory "*"

        exec "${@}"
    else
        groupmod -g "${GROUP_ID}" -n cime ubuntu
        usermod -d /home/cime -u "${USER_ID}" -g "${GROUP_ID}" -l cime ubuntu

        chown -R cime:cime /home/cime

        if [[ -n "${SRC_PATH}" ]] && [[ -e "${SRC_PATH}" ]]; then
            chown -R cime:cime "${SRC_PATH}"

            git config --global --add safe.directory "*"
        fi

        {
            echo "source /opt/conda/etc/profile.d/conda.sh"
            echo "conda activate base"
        } > /home/cime/.bashrc

        gosu "${USER_ID}" "${@}"
    fi
fi
