ARG BASE_TAG=24.3.0-0
FROM condaforge/miniforge3:${BASE_TAG} AS base

SHELL ["/bin/bash", "-c"]

# First layer as they never change, required for E3SM testing, TODO: fix in unittesting as well
RUN mkdir -p \
    /storage/inputdata/cpl/gridmaps/oQU240 \
    /storage/inputdata/share/domains \
    /storage/timings && \
    wget -O /storage/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc && \
    wget -O /storage/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc && \
    wget -O /storage/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc

COPY cime.yaml /cime.yaml

RUN mamba env update -f /cime.yaml && \
    rm -rf /opt/conda/pkgs/* && \
    ln -sf /opt/conda/bin/x86_64-conda-linux-gnu-ar /opt/conda/bin/ar && \
    ln -sf /opt/conda/bin/x86_64-conda-linux-gnu-ranlib /opt/conda/bin/ranlib

ARG PNETCDF_VERSION=1.12.3
ENV PNETCDF_VERSION=${PNETCDF_VERSION}

# Build pnetcdf
RUN curl -L -k -o "${PWD}/pnetcdf.tar.gz" \
            https://parallel-netcdf.github.io/Release/pnetcdf-${PNETCDF_VERSION}.tar.gz && \
            mkdir "${PWD}/pnetcdf" && \
            tar -xvf "${PWD}/pnetcdf.tar.gz" -C "${PWD}/pnetcdf" --strip-components=1 && \
            rm -rf "${PWD}/pnetcdf.tar.gz" && \
            cd "${PWD}/pnetcdf" && \
            source /opt/conda/etc/profile.d/conda.sh && \
            conda activate base && \
            ./configure --prefix /opt/conda --disable-cxx --enable-shared \
            MPICC=/opt/conda/bin/mpicc \
            MPICXX=/opt/conda/bin/mpicxx \
            MPIF77=/opt/conda/bin/mpif77 \
            MPIF90=/opt/conda/bin/mpif90 && \
            make -j4 && \
            make install && \
            rm -rf "${PWD}/pnetcdf"

ARG CIME_BRANCH=master
ARG CIME_REPO=https://github.com/esmci/cime

# Separate layer, it's most likely to change
RUN git clone -b ${CIME_BRANCH} ${CIME_REPO} /src/cime

# General variables
ENV USER=root
ENV LOGNAME=root
ENV ESMFMKFILE=/opt/conda/lib/esmf.mk
ENV SRC_PATH=/src

WORKDIR /src

COPY .cime /root/.cime
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

FROM base AS slurm

RUN apt-get update && \
            DEBIAN_FRONTEND=noninteractive \
            apt-get install -y --no-install-recommends \
            munge slurmd slurm-client slurmctld && \
            rm -rf /var/lib/apt/lists/* && \
            sed -i"" "s/\(.*<BATCH_SYSTEM>\)[^<]*\(<\/BATCH_SYSTEM>\)/\1slurm\2/g" ~/.cime/config_machines.xml

COPY slurm/slurm.conf /etc/slurm-llnl/
COPY slurm/config_batch.xml /root/.cime/
COPY slurm/entrypoint_batch.sh /entrypoint_batch.sh

FROM base AS pbs

RUN apt-get update && \
            DEBIAN_FRONTEND=noninteractive \
            apt-get install -y --no-install-recommends \
            curl ca-certificates software-properties-common \
            gcc make libtool libhwloc-dev libx11-dev libxt-dev libedit-dev \
            libical-dev ncurses-dev python-dev tcl-dev tk-dev swig libexpat-dev libssl-dev \
            libxext-dev libxft-dev autoconf automake \
            postgresql-12 postgresql-server-dev-all postgresql-contrib \
            expat libedit2 python3 sendmail-bin sudo tcl tk && \
            add-apt-repository ppa:deadsnakes/ppa && \
            apt-get update && \
            DEBIAN_FRONTEND=noninteractive \
            apt-get install -y python3.7 python3.7-dev && \
            rm -rf /var/lib/apt/lists/*

RUN mkdir /src && pushd /src && \
            curl -LO https://github.com/openpbs/openpbs/archive/refs/tags/v20.0.1.tar.gz && \
            tar -xvf v20.0.1.tar.gz  && \
            cd openpbs-20.0.1 && \
            sed -i"" 's/\(#include "list_link.h"\)/\1\n#include <stddef.h>/' /src/openpbs-20.0.1/src/lib/Libifl/list_link.c && \
            export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && \
            ./autogen.sh && \
            PYTHON=/usr/bin/python3.7 \
            CFLAGS="`/usr/bin/python3.7m-config --cflags`" \
            LDFLAGS="`/usr/bin/python3.7m-config --ldflags`" \
            LIBS="-lpthread -lm -lpython3.7m" \
            ./configure --prefix=/opt/pbs && \
            make -j8 && \
            make install && \
            popd && \
            rm -rf /src && \
            sed -i"" "s/\(.*<BATCH_SYSTEM>\)[^<]*\(<\/BATCH_SYSTEM>\)/\1pbs\2/g" ~/.cime/config_machines.xml

COPY pbs/pbs.conf /etc/
COPY pbs/config_batch.xml /root/.cime/
COPY pbs/entrypoint_batch.sh /entrypoint_batch.sh
