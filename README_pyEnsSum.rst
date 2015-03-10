===============
README.pyEnsSum
===============

This package is used to create a summary file for a  collection 
(or ensemble) of runs. The user must specify the location of the input files.
The summary file calculates global means, RMSZ scores, PCA loadings, and max errors.
This summary file is required for pyCECT.py.

This package includes:  
----------------------
     	pyEnsSum.py             
                            A script that generates an ensemble summary file 
     		            from a collection of files.

        pyEnsLib.py     
                            Library python script used by pyEnsSum.py

        pyEnsSum_test.sh        
                            Bsub script to submit pyEnsSum.py to yellowstone

        ens_excluded_varlist.json
                            The variable list that will excluded from
                            reading and processing


Before you start to use the package, you need to load the following modules: 
----------------------------------------------------------------------------
       - module load python 
       - module load numpy
       - module load scipy
       - module load pynio


To see all options (and defaults):
----------------------------------
       python pyEnsSum.py -h

Notes:
------
       For monthly average files, set tslice=0.

       For yearly average files, set tslice=1 (Because tslice ==0 is the initial conditions.)

       Esize can be less than or equal to the number of files in "--indir".

       Note that --res, --tag, --compset, and --mach only affect the metadata in the summary file.

       Recommended number of cores is 42. 

Examples for generating summary files:
--------------------------------------
	 (A) To generate (in parallel) a summary file for 151 simulations runs, 
       	 
           we specify the size and data location:
	    --esize 151
	    --indir /glade/u/tdd/asap/verification/cesm1_3_beta11/sz151-yellowstone-intel/

           We also specify the file to create for the summary:
 	    --sumfile intel_summary.nc 

	   Since these are yearly average files, we set
	    --tslice 1 

	   We also specify the tag (cesm1_3_beta110 that will be written to the
	   metadata of intel_summary.nc):
	    --tag cesm1_3_beta11

           We can exclude some variables from the analysis by specifying them in a json
	   file:
            --jsonfile ens_excluded_varlist.json
       
           To enable parallel mode:
            --mpi_enable    

           To generate global_mean and related variables:
            --gmonly

	   This yields the following command:

           mpirun.lsf python  pyEnsSum.py --verbose --esize 151 --tslice 1 --indir /glade/u/tdd/asap/verification/cesm1_3_beta11/sz151-yellowstone-intel/ --tag cesm1_3_beta11 --sumfile intel_test.nc --jsonfile ens_excluded_varlist.json --mpi_enable



	 (B) To generate (in serial) a summary file for 151 simulations runs, 

           python  pyEnsSum.py --verbose --esize 151 --tslice 1 --indir /glade/u/tdd/asap/verification/cesm1_3_beta11/sz151-yellowstone-intel/ --tag cesm1_3_beta11 --sumfile intel_test.nc --jsonfile ens_excluded_varlist.json

