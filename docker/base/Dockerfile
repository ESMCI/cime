# Build stage with Spack pre-installed and ready to be used
FROM spack/ubuntu-jammy:develop AS builder

# Install OS packages needed to build the software
RUN apt-get -yqq update && apt-get -yqq upgrade \
 && apt-get -yqq install gcc-11 g++-11 gfortran-11 \
 && rm -rf /var/lib/apt/lists/*

# What we want to install and how we want to install it
# is specified in a manifest file (spack.yaml)
RUN mkdir -p /opt/spack-environment && \
set -o noclobber \
&&  (echo spack: \
&&   echo '  specs:' \
&&   echo '  - hdf5@1.10.7+cxx+fortran+hl' \
&&   echo '  - netcdf-c@4.7.4+parallel-netcdf' \
&&   echo '  - netcdf-fortran@4.5.3' \
&&   echo '  - parallel-netcdf@1.11.0' \
&&   echo '  - intel-oneapi-mkl@2022.1.0+gfortran' \
&&   echo '  - openmpi@4.1.6' \
&&   echo '  config:' \
&&   echo '    template_dirs:' \
&&   echo '    - ./../templates' \
&&   echo '' \
&&   echo '    install_tree:' \
&&   echo '      root: /opt/software' \
&&   echo '  concretizer:' \
&&   echo '    unify: true' \
&&   echo '  view: /opt/views/view') > /opt/spack-environment/spack.yaml

# Install the software, remove unnecessary deps
RUN cd /opt/spack-environment && spack env activate . && spack install --fail-fast && spack gc -y

# Strip all the binaries
RUN find -L /opt/views/view/* -type f -exec readlink -f '{}' \; | \
    xargs file -i | \
    grep 'charset=binary' | \
    grep 'x-executable\|x-archive\|x-sharedlib' | \
    awk -F: '{print $1}' | xargs strip

# Modifications to the environment that are necessary to run
RUN cd /opt/spack-environment && \
    spack env activate --sh -d . > activate.sh


# Bare OS image to run the installed executables
FROM ubuntu:22.04

COPY --from=builder /opt/spack-environment /opt/spack-environment
COPY --from=builder /opt/software /opt/software
COPY --from=builder /opt/views /opt/views

RUN { \
      echo '#!/bin/sh' \
      && echo '.' /opt/spack-environment/activate.sh \
      && echo 'exec "$@"'; \
    } > /entrypoint.sh \
&& chmod a+x /entrypoint.sh \
&& ln -s /opt/views/view /opt/view


RUN apt-get -yqq update && apt-get -yqq upgrade \
 && apt-get -yqq install vim python3 python3-venv cmake make gosu wget curl subversion git gcc-11 g++-11 gfortran-11 \
 && rm -rf /var/lib/apt/lists/*


RUN groupadd -g 1000 cime \
    && useradd -g 1000 -m -u 1000 cime \
    && update-alternatives --install /usr/bin/gfortran gfortran /usr/bin/gfortran-11 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100

COPY .cime /home/cime/.cime
COPY entrypoint.sh /entrypoint.sh

RUN SKIP_ENTRYPOINT=true bash -c "source /entrypoint.sh && download_inputdata"

WORKDIR /home/cime

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "/bin/bash" ]
