#!/bin/bash

export USER_ID=${USER_ID:-1000}
export GROUP_ID=${GROUP_ID:-1000}

HOME_DIR="$(getent passwd ${USER_ID} | cut -d':' -f6)"
SKIP_SETUP="${SKIP_SETUP:-false}"
SKIP_EXEC="${SKIP_EXEC:-false}"

echo "Container configuration"
echo "USER_ID: ${USER_ID}"
echo "GROUP_ID: ${GROUP_ID}"
echo "HOME_DIR: ${HOME_DIR}"
echo "SKIP_SETUP: ${SKIP_SETUP}"
echo "SKIP_COMMAND: ${SKIP_COMMAND}"

function download_inputdata() {
    mkdir -p /home/cime/inputdata/cpl/gridmaps/oQU240 \
        /home/cime/inputdata/cpl/gridmaps/gx1v6 \
        /home/cime/inputdata/share/domains

    wget -O /home/cime/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.n
    wget -O /home/cime/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc
    wget -O /home/cime/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc
}

# Only required by E3SM for mct
function fix_mct_makefiles() {
    fix_arflags "${1}/mct/Makefile"
    fix_arflags "${1}/mpeu/Makefile"
    fix_arflags "${1}/mpi-serial/Makefile"
}

function fix_arflags() {
    if [[ ! -e "${1}.bak" ]]; then
        echo "Fixing AR variable in ${1}"

        sed -i".bak" "s/\$(AR)/\$(AR) cq/g" "${1}"
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

if [[ "${SKIP_SETUP}" == "false" ]]; then
    # will always be /home/cime due to config_machines.xml
    mkdir -p /home/cime/{timings,cases,archive,baselines,tools}

    if [[ "${USER_ID}" == "0" ]]; then
        export USER=root
        export LOGNAME=root

        echo "Copying /home/.cime -> ${HOME_DIR}/"

        cp -rf /home/cime/.cime "${HOME_DIR}/"
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
source /opt/spack-environment/activate.sh
EOF

    if [[ "${USER_ID}" == "0" ]]; then
        [[ "${SKIP_COMMAND}" == "false" ]] && exec "${@}"
    else
        fix_permissions /opt
        fix_permissions /home/cime

        if [[ -n "${SRC_PATH}" && -e "${SRC_PATH}" ]]; then
            fix_permissions "${SRC_PATH}"
        fi

        [[ "${SKIP_COMMAND}" ]] && gosu "${USER_ID}":"${GROUP_ID}" "${@}"
    fi
fi
