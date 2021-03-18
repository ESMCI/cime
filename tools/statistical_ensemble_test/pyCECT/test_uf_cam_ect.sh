#!/bin/tcsh
#PBS -A NIOW0001
#PBS -N UF-CAM-ECT
#PBS -q regular
#PBS -l select=1:ncpus=1:mpiprocs=1
#PBS -l walltime=0:15:00
#PBS -j oe
#PBS -M abaker@ucar.edu

setenv TMPDIR /glade/scratch/$USER/temp
mkdir -p $TMPDIR

python pyCECT.py --sumfile /glade/p/cisl/asap/pycect_sample_data/cam_c1.2.2.1/summary_files/uf.ens.c1.2.2.1_fc5.ne30.nc --indir /glade/p/cisl/asap/pycect_sample_data/cam_c1.2.2.1/uf_cam_test_files --tslice 1 --saveResults
