#!/bin/sh

# Get/Generate the Dashboard Model
if [ $# -eq 0 ]; then
	model=Experimental
else
	model=$1
fi

module rm PrgEnv-intel
module rm PrgEnv-cray
module rm PrgEnv-gnu
module rm intel
module rm cce
module rm cray-parallel-netcdf
module rm cray-parallel-hdf5
module rm pmi
module rm cray-libsci
module rm cray-mpich2
module rm cray-mpich
module rm cray-netcdf
module rm cray-hdf5
module rm cray-netcdf-hdf5parallel
module rm craype-sandybridge
module rm craype-ivybridge
module rm craype-haswell
module rm craype
module load PrgEnv-intel

case "$NERSC_HOST" in
    edison)
	module switch intel intel/16.0.0.109
	module load craype-ivybridge
	module load git/2.4.6
	module load cmake/3.3.2
	module load cray-hdf5-parallel/1.8.16 
	module load cray-netcdf-hdf5parallel/4.3.3.1
	module load cray-parallel-netcdf/1.7.0
	;;
    cori)
	module switch intel intel/17.0.1.132
	module load craype-mic-knl
	module load git/2.9.1
	module load cmake/3.3.2
	module load cray-hdf5-parallel/1.8.16
	module load cray-netcdf-hdf5parallel/4.3.3.1
	module load cray-parallel-netcdf/1.7.0
	;;
	
esac

export CC=cc
export FC=ftn

export PIO_DASHBOARD_ROOT=`pwd`/dashboard
export PIO_COMPILER_ID=Intel-`$CC --version | head -n 1 | cut -d' ' -f3`

if [ ! -d "$PIO_DASHBOARD_ROOT" ]; then
  mkdir "$PIO_DASHBOARD_ROOT"
fi
cd "$PIO_DASHBOARD_ROOT"

if [ ! -d src ]; then
  git clone --branch develop https://github.com/PARALLELIO/ParallelIO src
  cd src
else
  cd src
  git fetch origin
  git checkout develop
fi


ctest -S CTestScript.cmake,${model} -VV
