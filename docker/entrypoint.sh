#!/bin/bash

export USER_ID=${USER_ID:-1000}
export GROUP_ID=${GROUP_ID:-1000}

HOME_DIR="$(getent passwd ${USER_ID} | cut -d':' -f6)"
SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"

echo "Container configuration"
echo "USER_ID: ${USER_ID}"
echo "GROUP_ID: ${GROUP_ID}"
echo "HOME_DIR: ${HOME_DIR}"
echo "SKIP_ENTRYPOINT: ${SKIP_ENTRYPOINT}"

# Only required by E3SM for mct
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

function link_config_machines() {
    local src_path="/home/cime/.cime"

    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        echo "Linking E3SM ${src_path}/config_machines.v2.xml -> ${HOME_DIR}/.cime/config_machines.xml"

        ln -sf "${src_path}/config_machines.v2.xml" "${HOME_DIR}/.cime/config_machines.xml"
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        export ESMFMKFILE=/opt/conda/envs/cesm/lib/esmf.mk

        echo "Link CESM ${src_path}/config_machines.v3.xml -> ${HOME_DIR}/.cime/config_machines.xml"

        ln -sf "${src_path}/config_machines.v3.xml" "${HOME_DIR}/.cime/config_machines.xml"
    fi
}

function fix_permissions() {
    echo "Changing permissions to ${USER_ID}:${GROUP_ID} for ${1}"

    chown -R "${USER_ID}":"${GROUP_ID}" "${1}"
}

if [[ "${USER_ID}" == "0" ]]; then
    export USER=root
    export LOGNAME=root

    echo "Copying /home/.cime -> ${HOME_DIR}/"

    cp -ef /home/cime/.cime "${HOME_DIR}/"
else
    export USER=cime
    export LOGNAME=cime

    echo "Updating cime uid/gid to ${USER_ID}:${GROUP_ID}"

    # update the uid/gid for cime
    groupmod -g "${GROUP_ID}" cime
    usermod -u "${USER_ID}" cime
fi

link_config_machines

git config --global --add safe.directory "*"

cat << EOF > "${HOME_DIR}/.bashrc"
source /opt/conda/etc/profile.d/conda.sh
conda activate base

if [[ -n "\${CIME_MODEL}" ]]; then
    conda activate "\${CIME_MODEL}"
fi
EOF

if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    if [[ "${USER_ID}" == "0" ]]; then
        exec "${@}"
    else
        fix_permissions /home/cime

        if [[ -n "${SRC_PATH}" && -e "${SRC_PATH}" ]]; then
            fix_permissions "${SRC_PATH}"
        fi

        gosu "${USER_ID}":${GROUP_ID}" "${@}"
    fi
fi
