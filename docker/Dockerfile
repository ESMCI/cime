FROM ghcr.io/spack/ubuntu-noble:1.0.4 AS spack

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-openmp-dev \
    libopenblas0-openmp \
    libxml-libxml-perl \
    libxml2-utils \
    openmpi-bin \
    libopenmpi-dev \
    perl \
    pkg-config \
    python3-dev \
    subversion \
    wget \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /opt/spack-envs

COPY docker/spack.yaml /opt/spack-envs/spack.yaml

RUN spack compiler find \
  && spack external find --not-buildable \
  && spack external find --not-buildable openmpi \
  && spack -e /opt/spack-envs install --fail-fast

ENV PATH=/opt/spack-envs/view/bin:$PATH
ENV PKG_CONFIG_PATH=/opt/spack-envs/view/lib/pkgconfig
ENV LD_LIBRARY_PATH=/opt/spack-envs/view/lib
ENV ESMFMKFILE=/opt/spack-envs/view/lib/esmf.mk

FROM spack AS cprnc

COPY CIME/non_py/cprnc /src/cprnc
COPY docker/entrypoint.sh /entrypoint.sh

RUN SKIP_ENTRYPOINT=true source /entrypoint.sh \
  && CPRNC_DIR=/src/cprnc build_cprnc

FROM spack AS main

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    vim \
    neovim \
  && rm -rf /var/lib/apt/lists/*

COPY test-requirements.txt /requirements.txt

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && source ~/.local/bin/env \
  && uv python install 3.10 \
  && uv venv \
  && source .venv/bin/activate \
  && uv pip install -r /requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh

RUN SKIP_ENTRYPOINT=true source /entrypoint.sh \
  && mkdir -p /root/storage/{tools,inputdata,cases,timings,archive,baselines} \
  && download_input_data

COPY --from=cprnc /root/storage/tools/cprnc /root/storage/tools/cprnc
COPY docker/.cime /root/.cime

ENTRYPOINT ["/entrypoint.sh"]
