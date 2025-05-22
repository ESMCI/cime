FROM spack/ubuntu-jammy:develop AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc-12 \
        g++-12 \
        gfortran-12 \
        make \
        cmake \
        autoconf \
        automake \
        hwloc \
        libtool \
        pkgconf \
        m4 \
        python3-dev \
        openmpi-bin \
        libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100 \
    && update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-12 100

RUN mkdir -p /opt/spack-environment

COPY docker/spack.yaml /opt/spack-environment

WORKDIR /opt/spack-environment

RUN spack env activate . \
    && spack buildcache keys --install --trust \
    && spack external find --all --exclude openssl --exclude hwloc \
    && spack install --fresh-roots --fresh --fail-fast \
    && spack gc -y
    
RUN spack env activate --sh -d . > activate.sh

FROM ubuntu:22.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gosu \
        build-essential \
        gcc-12 \
        g++-12 \
        gfortran-12 \
        python3 \
        python3-pip \
        cmake \
        ca-certificates \
        wget \
        curl \
        subversion \
        git \
        vim \
        rsync \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-12 50

COPY --from=builder /opt/spack-environment /opt/spack-environment
COPY --from=builder /opt/software /opt/software
COPY --from=builder /opt/views /opt/views
COPY docker/helper.sh /helper.sh
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/.cime /home/cime_user/.cime
COPY test-requirements.txt /home/cime_user/test-requirements.txt

RUN ln -s /opt/views/view /opt/view \
    && python3 -m pip install -r /home/cime_user/test-requirements.txt

ENV USER=cime_user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash", "--rcfile", "/etc/profile", "-l"]
