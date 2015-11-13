#!/bin/bash
#BSUB -n 36 
#BSUB -q regular
#BSUB -R "span[ptile=2]"
#BSUB -a poe
#BSUB -N
#BSUB -x
#BSUB -o pop.%J.stdout
#BSUB -e pop.%J.stdout
#BSUB -J pop
#BSUB -P STDD0002
#BSUB -W 1:25
#BSUB -u haiyingx@ucar.edu

export MP_LABELIO=yes;
export MP_COREFILE_FORMAT=lite
mpirun.lsf python pyEnsSumPop.py --verbose --indir /glade/u/tdd/asap/pop_verification/ensemble_80/ --sumfile /glade/scratch/haiyingx/pop.ens.sum.2.nc --tslice 0 --nyear 3 --nmonth 12 --npert 80 --jsonfile pop_ensemble.json  --mpi_enable
