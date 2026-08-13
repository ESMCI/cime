# syntax=docker/dockerfile:1
#
# CIME CI container. Dependencies are provided by conda-forge via pixi (see
# docker/pixi.toml) instead of spack. Two pixi environments are baked in:
#   * e3sm - ships MOAB (tempest-remap)
#   * cesm - ships ESMF
# Both share an identical MPICH HDF5/netCDF/pnetcdf stack, which fixes the
# broken cprnc caused by spack pulling multiple netCDF copies into the graph.
#
# NOTE: BuildKit is required (the cache mounts below). Build with:
#   DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t cime .

ARG UBUNTU_DIGEST=sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea
ARG PIXI_VERSION=0.73.0
ARG PIXI_SHA256=682564e7cd35d38307df3cd6c8e9a45a1437d20febac0c8d165809d7c38408d1
ARG UV_VERSION=0.12.3
ARG UV_SHA256=600cf9a742aca00d292673b16b5acffaa7b8c269a364ad0c2e79498dcb1fe101

########################################################################
# Base image with the pixi environments installed at their final path. #
########################################################################
FROM ubuntu:24.04@${UBUNTU_DIGEST} AS base

ARG PIXI_VERSION
ARG PIXI_SHA256

# entrypoint.sh is bash (uses `source`, `[[ ]]`); ubuntu defaults sh->dash.
SHELL ["/bin/bash", "-c"]

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    libxml-libxml-perl \
    libxml2-utils \
    perl \
    subversion \
    wget \
  && rm -rf /var/lib/apt/lists/*

# Install a pinned pixi release (verified against a known checksum).
RUN curl -LsSf "https://github.com/prefix-dev/pixi/releases/download/v${PIXI_VERSION}/pixi-x86_64-unknown-linux-musl.tar.gz" \
      -o /tmp/pixi.tar.gz \
  && echo "${PIXI_SHA256}  /tmp/pixi.tar.gz" | sha256sum -c - \
  && tar -xzf /tmp/pixi.tar.gz -C /usr/local/bin pixi \
  && rm /tmp/pixi.tar.gz \
  && chmod +x /usr/local/bin/pixi

# Build the environments at the same path they will live at runtime so the
# conda prefixes (RPATHs, activation scripts) remain valid; conda prefixes are
# not relocatable, so we never move them after install.
WORKDIR /opt/pixi-env
COPY docker/pixi.toml docker/pixi.lock ./

# --frozen guarantees the committed pixi.lock is used verbatim. The rattler
# package cache is mounted so repeated builds skip re-downloading packages.
RUN --mount=type=cache,target=/root/.cache/rattler \
    pixi install --frozen -e e3sm -e cesm

##########################################
# Build cprnc against the e3sm netCDF.   #
# (libnetcdf is identical in both envs.) #
##########################################
FROM base AS cprnc

ENV CIME_MODEL=e3sm

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY CIME/non_py/cprnc /src/cprnc
COPY docker/entrypoint.sh /entrypoint.sh

RUN SKIP_ENTRYPOINT=true source /entrypoint.sh \
  && CPRNC_DIR=/src/cprnc build_cprnc

################################
# Final CI/development image.  #
################################
FROM base AS main

ARG UV_VERSION
ARG UV_SHA256

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    vim \
    neovim \
  && rm -rf /var/lib/apt/lists/*

COPY test-requirements.txt /requirements.txt

# Install a pinned uv release (verified against a known checksum), then use it
# to provide the Python test environment (pytest, etc.).
RUN curl -LsSf "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
      -o /tmp/uv.tar.gz \
  && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
  && tar -xzf /tmp/uv.tar.gz -C /usr/local/bin --strip-components=1 \
  && rm /tmp/uv.tar.gz \
  && chmod +x /usr/local/bin/uv /usr/local/bin/uvx \
  && uv python install 3.10 \
  && uv venv "${HOME}/.venv" \
  && source "${HOME}/.venv/bin/activate" \
  && uv pip install -r /requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh

# CIME_MODEL only needed so the entrypoint can source cleanly here; the input
# data download itself is model-agnostic. Cache mount at /tmp/inputdata-cache
# persists downloads across builds; files are copied into the final location so
# they persist in the image even when the cache expires.
# DOWNLOAD_SKIP_ON_ERROR=1 makes NERSC download failures non-fatal during build
# (GitHub Actions runners cannot reach portal.nersc.gov); missing files will be
# attempted again at container startup.
RUN --mount=type=cache,target=/tmp/inputdata-cache \
    CIME_MODEL=e3sm SKIP_ENTRYPOINT=true source /entrypoint.sh \
  && mkdir -p /root/storage/{tools,inputdata,cases,timings,archive,baselines} \
  && STORAGE_DIR=/tmp/inputdata-cache DOWNLOAD_SKIP_ON_ERROR=1 download_input_data \
  && cp -r /tmp/inputdata-cache/inputdata/* /root/storage/inputdata/ || true

COPY --from=cprnc /root/storage/tools/cprnc /root/storage/tools/cprnc
COPY docker/.cime /root/.cime

ENTRYPOINT ["/entrypoint.sh"]
