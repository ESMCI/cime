#!/usr/bin/env python
from __future__ import print_function
import configparser
import sys, getopt, os
import numpy as np
import netCDF4 as nc
import time
import re
from asaptools.partition import EqualStride, Duplicate
import asaptools.simplecomm as simplecomm
import pyEnsLib

def main(argv):


    # Get command line stuff and store in a dictionary
    s = 'nyear= nmonth= npert= tag= res= mach= compset= sumfile= indir= tslice= verbose jsonfile= mpi_enable mpi_disable nrand= rand seq= jsondir= esize='
    optkeys = s.split()
    try:
        opts, args = getopt.getopt(argv, "h", optkeys)
    except getopt.GetoptError:
        pyEnsLib.EnsSumPop_usage()
        sys.exit(2)

    # Put command line options in a dictionary - also set defaults
    opts_dict={}

    # Defaults
    opts_dict['tag'] = 'cesm2_1_0'
    opts_dict['compset'] = 'G'
    opts_dict['mach'] = 'cheyenne'
    opts_dict['tslice'] = 0
    opts_dict['nyear'] = 1
    opts_dict['nmonth'] = 12
    opts_dict['esize'] = 40
    opts_dict['npert'] = 0 #for backwards compatible
    opts_dict['nbin'] = 40
    opts_dict['minrange'] = 0.0
    opts_dict['maxrange'] = 4.0
    opts_dict['res'] = 'T62_g17'
    opts_dict['sumfile'] = 'pop.ens.summary.nc'
    opts_dict['indir'] = './'
    opts_dict['jsonfile'] = 'pop_ensemble.json'
    opts_dict['verbose'] = True
    opts_dict['mpi_enable'] = True
    opts_dict['mpi_disable'] = False
    #opts_dict['zscoreonly'] = True
    opts_dict['popens'] = True
    opts_dict['nrand'] = 40
    opts_dict['rand'] = False
    opts_dict['seq'] = 0
    opts_dict['jsondir'] = './'

    # This creates the dictionary of input arguments
    #print "before parseconfig"
    opts_dict = pyEnsLib.getopt_parseconfig(opts,optkeys,'ESP',opts_dict)

    verbose = opts_dict['verbose']
    nbin = opts_dict['nbin']

    if opts_dict['mpi_disable']:
        opts_dict['mpi_enable'] = False

    #still have npert for backwards compatibility - check if it was set
    #and override esize
    if opts_dict['npert'] > 0:
        user_size = opts_dict['npert']
        print('WARNING: User specified value for --npert will override --esize.  Please consider using --esize instead of --npert in the future.')
        opts_dict['esize'] = user_size

    # Now find file names in indir
    input_dir = opts_dict['indir']

    # Create a mpi simplecomm object
    if opts_dict['mpi_enable']:
        me=simplecomm.create_comm()
    else:
        me=simplecomm.create_comm(False)

    if opts_dict['jsonfile']:
        # Read in the included var list
        Var2d,Var3d=pyEnsLib.read_jsonlist(opts_dict['jsonfile'],'ESP')
        str_size=0
        for str in Var3d:
            if str_size < len(str):
               str_size=len(str)
        for str in Var2d:
            if str_size < len(str):
               str_size=len(str)

    if me.get_rank() == 0:
        print('STATUS: Running pyEnsSumPop!')

        if verbose:
            print("VERBOSE: opts_dict = ")
            print(opts_dict)

    in_files=[]
    if(os.path.exists(input_dir)):
        # Pick up the 'nrand' random number of input files to generate summary files
        if opts_dict['rand']:
           in_files=pyEnsLib.Random_pickup_pop(input_dir,opts_dict,opts_dict['nrand'])
        else:
           # Get the list of files
           in_files_temp = os.listdir(input_dir)
           in_files=sorted(in_files_temp)
        num_files = len(in_files)

    else:
        if me.get_rank() == 0:
            print('ERROR: Input directory: ',input_dir,' not found => EXITING....')
        sys.exit(2)

    #make sure we have enough files
    files_needed = opts_dict['nmonth'] * opts_dict['esize'] * opts_dict['nyear']
    if (num_files < files_needed):
        if me.get_rank() == 0:
            print('ERROR: Input directory does not contain enough files (must be esize*nyear*nmonth = ', files_needed, ' ) and it has only ', num_files, ' files).')
        sys.exit(2)



    #Partition the input file list (ideally we have one processor per month)
    in_file_list=me.partition(in_files,func=EqualStride(),involved=True)

    # Check the files in the input directory
    full_in_files=[]
    if me.get_rank() == 0 and opts_dict['verbose']:
        print('VERBOSE: Input files are:')

    for onefile in in_file_list:
        fname = input_dir + '/' + onefile
        if opts_dict['verbose']:
            print( "my_rank = ", me.get_rank(), "  ", fname)
        if (os.path.isfile(fname)):
            full_in_files.append(fname)
        else:
            print("ERROR: Could not locate file: "+ fname + " => EXITING....")
            sys.exit()


    #open just the first file (all procs)
    first_file = nc.Dataset(full_in_files[0],"r")

    # Store dimensions of the input fields
    if (verbose == True) and me.get_rank() == 0:
        print("VERBOSE: Getting spatial dimensions")
    nlev = -1
    nlat = -1
    nlon = -1

    # Look at first file and get dims
    input_dims = first_file.dimensions
    ndims = len(input_dims)

    # Make sure all files have the same dimensions
    if (verbose == True) and me.get_rank() == 0:
        print("VERBOSE: Checking dimensions ...")
    for key in input_dims:
        if key == "z_t":
            nlev = len(input_dims["z_t"])
        elif key == "nlon":
            nlon = len(input_dims["nlon"])
        elif key == "nlat":
            nlat = len(input_dims["nlat"])


    # Rank 0: prepare new summary ensemble file
    this_sumfile = opts_dict["sumfile"]
    if (me.get_rank() == 0 ):
        if os.path.exists(this_sumfile):
            os.unlink(this_sumfile)

        if verbose:
            print("VERBOSE: Creating ", this_sumfile, "  ...")

        nc_sumfile = nc.Dataset(this_sumfile, "w", format="NETCDF4_CLASSIC")

        # Set dimensions
        if verbose:
            print("VERBOSE: Setting dimensions .....")
        nc_sumfile.createDimension('nlat', nlat)
        nc_sumfile.createDimension('nlon', nlon)
        nc_sumfile.createDimension('nlev', nlev)
        nc_sumfile.createDimension('time',None)
        nc_sumfile.createDimension('ens_size', opts_dict['esize'])
        nc_sumfile.createDimension('nbin', opts_dict['nbin'])
        nc_sumfile.createDimension('nvars', len(Var3d) + len(Var2d))
        nc_sumfile.createDimension('nvars3d', len(Var3d))
        nc_sumfile.createDimension('nvars2d', len(Var2d))
        nc_sumfile.createDimension('str_size', str_size)

        # Set global attributes
        now = time.strftime("%c")
        if verbose:
            print("VERBOSE: Setting global attributes .....")
        nc_sumfile.creation_date = now
        nc_sumfile.title = 'POP verification ensemble summary file'
        nc_sumfile.tag =  opts_dict["tag"]
        nc_sumfile.compset = opts_dict["compset"]
        nc_sumfile.resolution = opts_dict["res"]
        nc_sumfile.machine =  opts_dict["mach"]

        # Create variables
        if verbose:
            print("VERBOSE: Creating variables .....")
        v_lev = nc_sumfile.createVariable("z_t", 'f', ('nlev',))
        v_vars = nc_sumfile.createVariable("vars", 'S1', ('nvars', 'str_size'))
        v_var3d = nc_sumfile.createVariable("var3d", 'S1', ('nvars3d', 'str_size'))
        v_var2d = nc_sumfile.createVariable("var2d", 'S1', ('nvars2d', 'str_size'))
        v_time = nc_sumfile.createVariable("time",'d',('time',))
        v_ens_avg3d = nc_sumfile.createVariable("ens_avg3d", 'f', ('time','nvars3d', 'nlev', 'nlat', 'nlon'))
        v_ens_stddev3d = nc_sumfile.createVariable("ens_stddev3d", 'f', ('time','nvars3d', 'nlev', 'nlat', 'nlon'))
        v_ens_avg2d = nc_sumfile.createVariable("ens_avg2d", 'f', ('time','nvars2d', 'nlat', 'nlon'))
        v_ens_stddev2d = nc_sumfile.createVariable("ens_stddev2d", 'f', ('time','nvars2d', 'nlat', 'nlon'))
        v_RMSZ = nc_sumfile.createVariable("RMSZ", 'f', ('time','nvars', 'ens_size','nbin'))


        # Assign vars, var3d and var2d
        if verbose:
            print("VERBOSE: Assigning vars, var3d, and var2d .....")

        eq_all_var_names =[]
        eq_d3_var_names = []
        eq_d2_var_names = []
        all_var_names = list(Var3d)
        all_var_names += Var2d
        l_eq = len(all_var_names)
        for i in range(l_eq):
            tt = list(all_var_names[i])
            l_tt = len(tt)
            if (l_tt < str_size):
                extra = list(' ')*(str_size - l_tt)
                tt.extend(extra)
            eq_all_var_names.append(tt)

        l_eq = len(Var3d)
        for i in range(l_eq):
            tt = list(Var3d[i])
            l_tt = len(tt)
            if (l_tt < str_size):
                extra = list(' ')*(str_size - l_tt)
                tt.extend(extra)
            eq_d3_var_names.append(tt)

        l_eq = len(Var2d)
        for i in range(l_eq):
            tt = list(Var2d[i])
            l_tt = len(tt)
            if (l_tt < str_size):
                extra = list(' ')*(str_size - l_tt)
                tt.extend(extra)
            eq_d2_var_names.append(tt)

        v_vars[:] = eq_all_var_names[:]
        v_var3d[:] = eq_d3_var_names[:]
        v_var2d[:] = eq_d2_var_names[:]

        # Time-invarient metadata
        if verbose:
            print("VERBOSE: Assigning time invariant metadata .....")
        vars_dict = first_file.variables
        lev_data = vars_dict["z_t"]
        v_lev[:] = lev_data[:]

        #end of rank 0

    #All:
    # Time-varient metadata
    if verbose:
        if me.get_rank() == 0:
            print("VERBOSE: Assigning time variant metadata .....")
    vars_dict = first_file.variables
    time_value = vars_dict['time']
    time_array = np.array([time_value])
    time_array = pyEnsLib.gather_npArray_pop(time_array,me,(me.get_size(),))
    if me.get_rank() == 0:
        v_time[:]=time_array[:]

    #Assign zero values to first time slice of RMSZ and avg and stddev for 2d & 3d
    #in case of a calculation problem before finishing
    e_size = opts_dict['esize']
    b_size =  opts_dict['nbin']
    z_ens_avg3d=np.zeros((len(Var3d),nlev,nlat,nlon),dtype=np.float32)
    z_ens_stddev3d=np.zeros((len(Var3d),nlev,nlat,nlon),dtype=np.float32)
    z_ens_avg2d=np.zeros((len(Var2d),nlat,nlon),dtype=np.float32)
    z_ens_stddev2d=np.zeros((len(Var2d),nlat,nlon),dtype=np.float32)
    z_RMSZ = np.zeros(((len(Var3d)+len(Var2d)),e_size,b_size), dtype=np.float32)

    #rank 0 (put zero values in summary file)
    if me.get_rank() == 0 :
        v_RMSZ[0,:,:,:]=z_RMSZ[:,:,:]
        v_ens_avg3d[0,:,:,:,:]=z_ens_avg3d[:,:,:,:]
        v_ens_stddev3d[0,:,:,:,:]=z_ens_stddev3d[:,:,:,:]
        v_ens_avg2d[0,:,:,:]=z_ens_avg2d[:,:,:]
        v_ens_stddev2d[0,:,:,:]=z_ens_stddev2d[:,:,:]

    #close file[0]
    first_file.close()

    # Calculate RMSZ scores
    if (verbose == True and me.get_rank() == 0):
        print("VERBOSE: Calculating RMSZ scores .....")

    zscore3d,zscore2d,ens_avg3d,ens_stddev3d,ens_avg2d,ens_stddev2d=pyEnsLib.calc_rmsz(full_in_files,Var3d,Var2d,opts_dict)

    if (verbose == True and me.get_rank() == 0):
        print("VERBOSE: Finished with RMSZ scores .....")

    # Collect from all processors
    if opts_dict['mpi_enable'] :
        # Gather the 3d variable results from all processors to the master processor

        zmall=np.concatenate((zscore3d,zscore2d),axis=0)
        zmall=pyEnsLib.gather_npArray_pop(zmall,me,(me.get_size(),len(Var3d)+len(Var2d),len(full_in_files),nbin))

        ens_avg3d=pyEnsLib.gather_npArray_pop(ens_avg3d,me,(me.get_size(),len(Var3d),nlev,(nlat),nlon))
        ens_avg2d=pyEnsLib.gather_npArray_pop(ens_avg2d,me,(me.get_size(),len(Var2d),(nlat),nlon))
        ens_stddev3d=pyEnsLib.gather_npArray_pop(ens_stddev3d,me,(me.get_size(),len(Var3d),nlev,(nlat),nlon))
        ens_stddev2d=pyEnsLib.gather_npArray_pop(ens_stddev2d,me,(me.get_size(),len(Var2d),(nlat),nlon))

    # Assign to summary file:
    if me.get_rank() == 0 :

        v_RMSZ[:,:,:,:]=zmall[:,:,:,:]
        v_ens_avg3d[:,:,:,:,:]=ens_avg3d[:,:,:,:,:]
        v_ens_stddev3d[:,:,:,:,:]=ens_stddev3d[:,:,:,:,:]
        v_ens_avg2d[:,:,:,:]=ens_avg2d[:,:,:,:]
        v_ens_stddev2d[:,:,:,:]=ens_stddev2d[:,:,:,:]

        print("STATUS: PyEnsSumPop has completed.")

        nc_sumfile.close()


if __name__ == "__main__":
    main(sys.argv[1:])
