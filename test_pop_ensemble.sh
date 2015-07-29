#!/bin/bash
#BSUB -n 12 
#BSUB -q regular
#BSUB -R "span[ptile=2]"
#BSUB -a poe
#BSUB -N
#BSUB -x
#BSUB -o pop.%J.stdout
#BSUB -e pop.%J.stdout
#BSUB -J pop
#BSUB -P STDD0002
#BSUB -W 4:25
#BSUB -u haiyingx@ucar.edu

export MP_LABELIO=yes;
export MP_COREFILE_FORMAT=lite
#export MP_DEBUG_TIMEOUT_COMMAND=~/bin/timeout_debug.sh
mpirun.lsf python pyEnsSumPop.py --verbose --indir /glade/scratch/haiyingx/pop_ensemble_data/ --sumfile /glade/scratch/haiyingx/pop.ens.sum.nc --nyear 1 --nmonth 12 --npert 40 --jsonfile pop_ensemble.json  --mpi_enable --nbin 40

