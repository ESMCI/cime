#!/bin/tcsh
#PBS -A NIOW0001
#PBS -N ensSumPop
#PBS -q regular
#PBS -l select=4:ncpus=3:mpiprocs=3
#PBS -l walltime=0:20:00
#PBS -j oe
#PBS -M abaker@ucar.edu


mpiexec_mpt python pyEnsSumPop.py --verbose --indir  /glade/p/cisl/asap/pycect_sample_data/pop_c2.0.b10/pop_ens_files --sumfile pop.cesm2.0.b10.nc --tslice 0 --nyear 1 --nmonth 12 --esize 40 --jsonfile pop_ensemble.json  --mach cheyenne --compset G --tag cesm2_0_beta10 --res T62_g17
