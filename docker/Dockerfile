FROM ghcr.io/spack/ubuntu-noble:1.0.4 AS builder

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
COPY docker/.cime /root/.cime

RUN SKIP_ENTRYPOINT=true source /entrypoint.sh \
  && download_input_data

ENTRYPOINT ["/entrypoint.sh"]
