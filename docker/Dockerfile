ARG BASE_TAG=latest
FROM condaforge/miniforge3:${BASE_TAG} AS base

WORKDIR /home/cime

RUN mkdir -p \
        /home/cime/inputdata/cpl/gridmaps/oQU240 \
        /home/cime/inputdata/share/domains \
        /home/cime/timings \
        /home/cime/cases \
        /home/cime/archive \
        /home/cime/baselines \
        /home/cime/tools \
    && wget -O /home/cime/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/cpl/gridmaps/oQU240/map_oQU240_to_ne4np4_aave.160614.nc \
    && wget -O /home/cime/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.ocn.ne4np4_oQU240.160614.nc \
    && wget -O /home/cime/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc \
        https://portal.nersc.gov/project/e3sm/inputdata/share/domains/domain.lnd.ne4np4_oQU240.160614.nc

COPY cime.yaml cime.yaml

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
    perl libxml-libxml-perl && \
    rm -rf /var/lib/apt/lists/*

RUN mamba install -y gosu tree

RUN mamba create -n e3sm -y --file cime.yaml python=3.10 'libnetcdf=4.9.1=*openmpi*' \
    && conda remove -n e3sm --force perl \
    && conda clean -afy \
    && rm -rf /opt/conda/pkgs/*

RUN mamba create -n cesm -y --file cime.yaml python=3.10 'libnetcdf>=4.9.2=*openmpi*' \
    && conda remove -n cesm --force perl \
    && conda clean -afy \
    && rm -rf /opt/conda/pkgs/*

COPY .cime .cime
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
