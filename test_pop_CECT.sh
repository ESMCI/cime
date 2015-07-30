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
mpirun.lsf python pyCECT.py --sumfile /glade/scratch/haiyingx/pop.ens.sum.nc --indir /glade/scratch/haiyingx/test_pop_data/ --popens --jsonfile pop_ensemble.json --mpi_enable

