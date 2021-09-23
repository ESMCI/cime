FROM ubuntu:20.10 as cesm

ENV USER=root
ENV CIME_MODEL=cesm
ENV NETCDF_FORTRAN_VERSION=4.5.2
ENV PNETCDF_VERSION=1.12.1
ENV PATH=/build/local/bin:$PATH

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /build

RUN apt update && \
      apt install -y --no-install-recommends \
        python3 \
        git \
        vim \
        build-essential \
        gcc-9 \
        g++-9 \
        gfortran-9 \
        openmpi-bin \
        libopenmpi-dev \
        libcurl4-openssl-dev \
        libnetcdf-dev \
        netcdf-bin \
        libxml2-utils \
        pylint \
        cmake \
        curl \
        wget \
        subversion \
        ca-certificates \
      pkg-config && \
      rm -rf /var/lib/apt/lists && \
      update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && \
      update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 10 && \
      update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 10 && \
      update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-9 10 && \
      curl -L -k -o netcdf-fortran.tar.gz \
      https://github.com/Unidata/netcdf-fortran/archive/refs/tags/v${NETCDF_FORTRAN_VERSION}.tar.gz && \
      mkdir "${PWD}/netcdf-fortran" && \
      tar -xvf "${PWD}/netcdf-fortran.tar.gz" -C "${PWD}/netcdf-fortran" --strip-components=1 && \
      cd "${PWD}/netcdf-fortran" && \
      ./configure --prefix=/build/local && \
      make && \
      make install && \
      curl -L -k -o pnetcdf.tar.gz \
      https://parallel-netcdf.github.io/Release/pnetcdf-${PNETCDF_VERSION}.tar.gz && \
      mkdir "${PWD}/pnetcdf" && \
      tar -xvf "${PWD}/pnetcdf.tar.gz" -C "${PWD}/pnetcdf" --strip-components=1 && \
      cd "${PWD}/pnetcdf" && \
      ./configure --prefix=/build/local --enable-shared --disable-cxx && \
      make && \
      make install && \
      cd "/build/local/include" && \
      ln -sf /usr/include/*netcdf* . && \
      cd "/build/local/lib" && \
      ln -sf `nc-config --libdir`/lib* .

WORKDIR /root

RUN git clone https://github.com/ESMCI/cime && \
      cd cime && \
      git clone https://github.com/ESCOMP/CMEPS components/cmeps && \
      git clone https://github.com/ESCOMP/CDEPS components/cdeps && \
      git clone https://github.com/ESCOMP/CESM_CPL7andDataComps components/cpl7 && \
      git clone https://github.com/ESCOMP/CESM_share share/ && \
      git clone https://github.com/MCSclimate/MCT libraries/mct && \
      git clone https://github.com/NCAR/ParallelIO libraries/parallelio

RUN mkdir  ~/.cime

WORKDIR /root/cime/scripts

COPY config_machines.xml /root/cime_config/machines/
COPY config_compilers.xml /root/cime_config/machines/

FROM condaforge/mambaforge:latest AS e3sm

ENV USER=root
ENV CIME_MODEL=e3sm
ENV PNETCDF_VERSION=1.12.1

WORKDIR /root

RUN git clone https://github.com/E3SM-Project/E3SM && \
      cd E3SM && \
      sed -i"" "s/git@github.com:/https:\/\/github.com\//g" .gitmodules && \
      git submodule update --init

RUN mamba install -c conda-forge \
      libnetcdf=*=*openmpi* \
      netcdf-fortran=*=*openmpi* \
      cmake \
      make \
      wget \
      curl \
      subversion \
      m4 \
      gcc_linux-64 \
      gxx_linux-64 \
      gfortran_linux-64 \
      openmpi-mpifort

SHELL ["/bin/bash", "-c"]

RUN curl -L -k -o pnetcdf.tar.gz \
      https://parallel-netcdf.github.io/Release/pnetcdf-${PNETCDF_VERSION}.tar.gz && \
      mkdir "${PWD}/pnetcdf" && \
      tar -xvf "${PWD}/pnetcdf.tar.gz" -C "${PWD}/pnetcdf" --strip-components=1 && \
      cd "${PWD}/pnetcdf" && \
      source /opt/conda/etc/profile.d/conda.sh && \
      conda activate base && \
      ./configure --prefix /opt/conda --disable-cxx --enable-shared \
      MPICC=/opt/conda/bin/mpicc \
      MPICXX=/opt/conda/bin/mpicxx \
      MPIF77=/opt/conda/bin/mpif77 \
      MPIF90=/opt/conda/bin/mpif90 && \
      make -j4 && \
      make install

RUN find /root/E3SM -type f -iname Makefile -exec grep -nH '$(AR) $@' {} \; | \
          cut -d":" -f1 | \
          xargs sed -i'' 's/$(AR) $@/$(AR) rc $@/g'

RUN ln -sf /opt/conda/bin/x86_64-conda-linux-gnu-ar /opt/conda/bin/ar && \
          ln -sf /opt/conda/bin/x86_64-conda-linux-gnu-ranlib /opt/conda/bin/ranlib

WORKDIR /root/E3SM/cime/scripts

COPY config_machines.xml /root/.cime/
COPY config_compilers.xml /root/.cime/
