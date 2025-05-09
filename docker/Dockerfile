FROM spack/ubuntu-jammy:develop AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc-12 \
        g++-12 \
        gfortran-12 \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-12 50

RUN mkdir -p /opt/spack-environment

COPY spack.yaml /opt/spack-environment

WORKDIR /opt/spack-environment

RUN spack env activate . && spack buildcache keys --install --trust &&  spack install --fail-fast && spack gc -y
 
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
        python3-pytest \
        python3-yaml \
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
COPY helper.sh /helper.sh
COPY entrypoint.sh /entrypoint.sh

RUN ln -s /opt/views/view /opt/view

ENV USER=cime_user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash", "--rcfile", "/etc/profile", "-l"]