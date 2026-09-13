#!/bin/bash
set -Eeuo pipefail

# Use fixed paths for container resources, regardless of user namespace mapping
# This ensures tools work with both Docker (root) and Podman (--userns=keep-id)
CONTAINER_HOME="/root"
export HOME="${CONTAINER_HOME}"
export USER="$(id -nu)"
export LOGNAME="${USER}"

SKIP_ENTRYPOINT="${SKIP_ENTRYPOINT:-false}"
STORAGE_DIR="${CONTAINER_HOME}/storage"

# Make files in storage directory accessible from host in real-time
# Set permissive umask so all new files are world-readable/writable
if [[ -d "${STORAGE_DIR}" ]]; then
    umask 000
    chmod -R a+rwX "${STORAGE_DIR}" 2>/dev/null || true
fi

# Root directory holding the per-model pixi environments (see docker/pixi.toml).
# Each model gets its own conda prefix built from conda-forge: e3sm ships MOAB,
# cesm ships ESMF. Both share an identical HDF5/netCDF/pnetcdf stack.
export PIXI_ENV_ROOT="${PIXI_ENV_ROOT:-/opt/pixi-env/.pixi/envs}"


# Fail fast when CIME_MODEL is unset or invalid; the pixi environment to activate
# and the config_machines file to link are both selected from it.
function require_cime_model() {
    if [[ -z "${CIME_MODEL:-}" ]]; then
        echo "ERROR: CIME_MODEL is not set. Set it to 'e3sm' or 'cesm'." >&2
        exit 1
    fi

    if [[ "${CIME_MODEL}" != "e3sm" && "${CIME_MODEL}" != "cesm" ]]; then
        echo "ERROR: CIME_MODEL='${CIME_MODEL}' is invalid. Must be 'e3sm' or 'cesm'." >&2
        exit 1
    fi

    local prefix="${PIXI_ENV_ROOT}/${CIME_MODEL}"
    if [[ ! -d "${prefix}" ]]; then
        echo "ERROR: Pixi environment not found at ${prefix}" >&2
        exit 1
    fi
}


# Compute the usable CPU count for the container, accounting for cgroup limits
# (docker run --cpus / --cpuset-cpus). Exported as DOCKER_MAX_TASKS so
# config_machines.xml can reference it via $ENV{DOCKER_MAX_TASKS}. This prevents
# the default PE layout + test proc pool from exceeding available cores, which
# causes either pool-overflow test failures or MPICH busy-poll livelocks.
function compute_container_cores() {
    local cores=""

    # Try cgroup v2 (unified hierarchy) cpu.max first (format: "$quota $period")
    if [[ -r /sys/fs/cgroup/cpu.max ]]; then
        local quota period
        read -r quota period < /sys/fs/cgroup/cpu.max
        if [[ "$quota" != "max" ]] && [[ -n "$period" ]] && [[ "$period" -gt 0 ]]; then
            cores=$(( (quota + period - 1) / period ))  # ceiling division
        fi
    fi

    # Fall back to cgroup v1 if v2 didn't yield a quota
    if [[ -z "$cores" ]] && [[ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]]; then
        local quota period
        quota=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo "-1")
        period=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo "100000")
        if [[ "$quota" -gt 0 ]] && [[ "$period" -gt 0 ]]; then
            cores=$(( (quota + period - 1) / period ))
        fi
    fi

    # Final fallback: nproc (respects --cpuset-cpus but not --cpus quota)
    if [[ -z "$cores" ]] || [[ "$cores" -le 0 ]]; then
        cores=$(nproc)
    fi

    export DOCKER_MAX_TASKS="$cores"
}


# Put the CIME_MODEL-specific pixi environment on the compiler/linker search
# paths. ESMFMKFILE is exported unconditionally; it only exists in the cesm
# environment and is simply ignored by e3sm builds.
function activate_pixi_env() {
    require_cime_model

    local prefix="${PIXI_ENV_ROOT}/${CIME_MODEL}"

    export PATH="${prefix}/bin:${PATH}"
    export PKG_CONFIG_PATH="${prefix}/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
    export LD_LIBRARY_PATH="${prefix}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
    export ESMFMKFILE="${prefix}/lib/esmf.mk"

    # MPICH pulls in UCX, whose transport init divides by a network
    # interface's link speed. Container virtual interfaces report a speed of
    # 0, which raises SIGFPE. Restrict UCX to shared-memory + self transports;
    # that is all that is needed for single-node (single container) runs and
    # avoids probing the offending interfaces entirely.
    export UCX_TLS="${UCX_TLS:-sm,self}"
}

# Build the cprnc tool from CIME sources
function build_cprnc() {
    cprnc_dir="${CPRNC_DIR:-${PWD}/CIME/non_py/cprnc}"
    tools_dir="${STORAGE_DIR}/tools"

    if [[ ! -e "${cprnc_dir}" ]]; then
        echo "CPRNC path does not exist. Change to CIME's root directory."
        exit 1
    fi

    pushd "$(mktemp -d)" || exit 1

    cmake -S "${cprnc_dir}" -B .

    make

    [[ ! -e "${tools_dir}" ]] && mkdir -p "${tools_dir}"

    # Needs to be copied into the machines configured tool path
    cp cprnc "${tools_dir}/cprnc"

    popd || exit 1
}


# Download input data needed for model setup
# required for grid generation tests
function download_input_data() {
    local skip_on_error="${DOWNLOAD_SKIP_ON_ERROR:-0}"

    mkdir -p "${STORAGE_DIR}/inputdata/cpl/gridmaps/oQU240"
    mkdir -p "${STORAGE_DIR}/inputdata/share/domains"

    # wget with retries, timeout, and continue on partial downloads
    local wget_opts=(
        --tries=5
        --timeout=30
        --waitretry=10
        --continue
        --no-verbose
    )

    local files=(
        "${STORAGE_DIR}/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc|https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc"
        "${STORAGE_DIR}/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc|https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc"
        "${STORAGE_DIR}/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc|https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc"
    )

    local failed=0
    for file_spec in "${files[@]}"; do
        local dest="${file_spec%%|*}"
        local url="${file_spec##*|}"

        # Skip if file already exists
        if [[ -f "$dest" ]]; then
            echo "Already present: $(basename "$dest")"
            continue
        fi

        echo "Downloading $(basename "$dest")..."
        if ! wget "${wget_opts[@]}" -O "$dest" "$url"; then
            echo "WARNING: Failed to download $url after retries" >&2
            # Clean up partial download
            rm -f "$dest"
            failed=1
        fi
    done

    if [[ $failed -eq 1 ]]; then
        if [[ $skip_on_error -eq 1 ]]; then
            echo "WARNING: Some input data files failed to download (non-fatal during build)" >&2
            return 0
        else
            echo "ERROR: One or more input data files failed to download" >&2
            return 1
        fi
    fi
}


# Link correct config_machines file based on CIME_MODEL, also set ESMFMKFILE for cesm
function link_config_machines() {
    # Skip when ~/.cime has not been populated yet (e.g. during image build,
    # before docker/.cime is copied in).
    [[ -d "${HOME}/.cime" ]] || return 0

    if [[ "${CIME_MODEL}" == "e3sm" ]]; then
        ln -sf "${CONTAINER_HOME}/.cime/config_machines.v2.xml" "${CONTAINER_HOME}/.cime/config_machines.xml"
    elif [[ "${CIME_MODEL}" == "cesm" ]]; then
        ln -sf "${CONTAINER_HOME}/.cime/config_machines.v3.xml" "${CONTAINER_HOME}/.cime/config_machines.xml"
    fi
}

activate_pixi_env
compute_container_cores

# Write DOCKER_MAX_TASKS to profile scripts so it's available in all shells.
# Only write if we have permission (skip for non-root or read-only containers).
if [[ -w /etc/profile.d/ ]]; then
    echo "export DOCKER_MAX_TASKS=${DOCKER_MAX_TASKS}" > /etc/profile.d/docker-max-tasks.sh
fi
if [[ -w /etc/bash.bashrc ]]; then
    echo "export DOCKER_MAX_TASKS=${DOCKER_MAX_TASKS}" >> /etc/bash.bashrc
fi

# Resolve absolute paths to handle symlinks and relative paths correctly
if [[ "${CI:-false}" == "true" ]]; then
  DOT_CIME_SRC=$(readlink -f /root/.cime)
  DOT_CIME_DST=$(readlink -f "${HOME}/.cime")
  if [[ "$SRC" != "$DST" ]]; then
    cp -rf /root/.cime "${HOME}"
  fi
fi

link_config_machines

# Attempt to download missing input data at runtime (if NERSC was unreachable
# during build, or if user is mounting a fresh storage directory).
# This runs silently in the background and does not block container startup.
if [[ "${SKIP_ENTRYPOINT}" == "false" ]] && [[ ! -f "${STORAGE_DIR}/inputdata/.download_complete" ]]; then
    (
        if download_input_data >/dev/null 2>&1; then
            touch "${STORAGE_DIR}/inputdata/.download_complete"
        fi
    ) &
fi

# Allow git to operate in any directory, for container/dev scenarios
if [[ -e "${PWD}/.git" ]]; then
    git config --global --add safe.directory "*"
fi

if [[ "${CI:-false}" == "false" ]] && [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
  source ${CONTAINER_HOME}/.venv/bin/activate
fi

if [[ "${SKIP_ENTRYPOINT}" == "false" ]]; then
    exec "${@}"
fi
