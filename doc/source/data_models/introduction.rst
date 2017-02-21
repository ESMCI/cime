.. _data-model-introduction:

Introduction
============

--------
Overview
--------
The CIME data models perform the basic function of reading external data files, modifying those data, and then sending the data to the driver/coupler via the CIME coupling interfaces.
The fields sent to the coupler are the same as those that would be sent by an active component.
This takes advantage of the fact that the driver/coupler and other models have no fundamental knowledge of whether another component is fully active or just a data model.
So, for example, the data atmosphere model (datm) sends the same fields as the prognostic Community Atmosphere Model (CAM).
However, rather than determining these fields prognostically, most data models simply read prescribed data.

The data models typically read gridded data from observations or reanalysis products.
Out of the box, they often provide a few possible data sources and/or time periods that you can choose from when setting up a case.
However, data models can also be configured to read output from a previous coupled run.
For example, you can perform a fully-coupled run in which you ask for particular extra output streams; you can then use these saved "coupler history" files as inputs to datm to run a later land-only spinup.

In some cases, data models have prognostic functionality, that is, they also receive and use data sent by the driver/coupler.
However, in most cases, the data models are not running prognostically and have no need to receive any data from the driver/coupler.

The CIME data models have parallel capability and share significant amounts of source code. 
Methods for reading and interpolating data have been established and can easily be reused:
The data model calls strdata ("stream data") methods which then call stream methods. 
The stream methods are responsible for managing lists of input data files and their time axis. 
The information is then passed up to the strdata methods where the data is read and interpolated in space and time. 
The interpolated data is passed up to the data model where final fields are derived, packed, and returned to the coupler.

------
Design
------
The strdata implementation is hardwired to execute a set of specific operations associated with reading and interpolating data in space and time. 
The strdata implementation does the following:

1. determines nearest lower and upper bound data from the input dataset 
2. if that is new data then read lower and upper bound data
3. fill lower and upper bound data
4. spatially map lower and upper bound data to model grid
5. time interpolate lower and upper bound data to model time
6. return fields to data model

----------------------
IO Through Data Models
----------------------
The two timestamps of input data that bracket the present model time are read first.
These are called the lower and upper bounds of data and will change as the model advances. 
Those two sets of inputdata are first filled based on the user setting of the namelist variables ``str_fillalgo`` and ``str_fillmask``. 
That operation occurs on the input data grid.
The lower and upper bound data are then spatially mapped to the model grid based upon the user setting of the namelist variables ``str_mapalgo`` and ``str_mapmask``. 
Spatial interpolation only occurs if the input data grid and model grid are not the identical, and this is determined in the strdata module automatically.
Time interpolation is the final step and is done using a time interpolation method specified by the user in namelist (via the shr_strdata_nml namelist variable "tintalgo"). 
A final set of fields is then available to the data model on the model grid and for the current model time.

There are two primary costs associated with strdata, reading data and spatially mapping data.
Time interpolation is relatively cheap in the current implementation. 
As much as possible, redundant operations are minimized.
Fill and mapping weights are generated at initialization and saved. 
The upper and lower bound mapped input data is saved between time steps to reduce mapping costs in cases where data is time interpolated more often than new data is read.
If the input data timestep is relatively small (for example, hourly data as opposed to daily or monthly data) the cost of reading input data can be quite large. 
Also, there can be significant variation in cost of the data model over the coarse of the run, for instance, when new inputdata must be read and interpolated, although it's relatively predictable.
The present implementation doesn't support changing the order of operations, for instance, time interpolating the data before spatial mapping. 
Because the present computations are always linear, changing the order of operations will not fundamentally change the results.
The present order of operations generally minimizes the mapping cost for typical data model use cases.

There are several limitations in both options and usage within the data models at the present time.
Spatial interpolation can only be performed from a two-dimensional latitude-longitude input grid. 
The target grid can be arbitrary but the source grid must be able to be described by simple one-dimensional lists of longitudes and latitudes, although they don't have to have equally spaced.

At the present time, data models can only read netcdf data, and IO is handled through either standard netcdf interfaces or through the PIO library using either netcdf or pnetcdf.
If standard netcdf is used, global fields are read and then scattered one field at a time. 
If PIO is used, then data will be read either serially or in parallel in chunks that are approximately the global field size divided by the number of io tasks.
If pnetcdf is used through PIO, then the pnetcdf library must be included during the build of the model. 
The pnetcdf path and option is hardwired into the ``Macros.make`` file for the specific machine.
To turn on ``pnetcdf`` in the build, make sure the ``Macros.make`` variables PNETCDF_PATH, INC_PNETCDF, and LIB_PNETCDF are set and that the PIO CONFIG_ARGS sets the PNETCDF_PATH argument. 

Beyond just the option of selecting IO with PIO, several namelist are available to help optimize PIO IO performance.
Those are **TODO** - list these. 
The total mpi tasks that can be used for IO is limited to the total number of tasks used by the data model.
Often though, fewer io tasks result in improved performance. 
In general, [io_root + (num_iotasks-1)*io_stride + 1] has to be less than the total number of data model tasks.
In practice, PIO seems to perform optimally somewhere between the extremes of 1 task and all tasks, and is highly machine and problem dependent.

-------------
Restart Files
-------------
Restart files are generated automatically by the data models based upon a flag sent from the coupler. 
The restart files must meet the CIME naming convention and an ``rpointer`` file is generated at the same time. 
An ``rpointer`` file is a *restart pointer* file which contains the name of the most recently created restart file. 
Normally, if restart files are read, the restart filenames are specified in the rpointer file. 
Optionally though, there are namelist variables such as `restfilm`` to specify the restart filenames via namelist. If those namelist are set, the ``rpointer`` file will be ignored. 
The default method is to use the ``rpointer`` files to specify the restart filenames. 
In most cases, no model restart is required for the data models to restart exactly. 
This is because there is no memory between timesteps in many of the data model science modes. 
If a model restart is required, it will be written automatically and then must be used to continue the previous run.

There are separate stream restart files that only exist for performance reasons. 
A stream restart file contains information about the time axis of the input streams. 
This information helps reduce the start costs associated with reading the input dataset time axis information. 
If a stream restart file is missing, the code will restart without it but may need to reread data from the input data files that would have been stored in the stream restart file. 
This will take extra time but will not impact the results.

---------
Hierarchy
---------
The hierarchy of data models, strdata, and streams also compartmentalize grids and fields. 
Data models communicate with the coupler with fields on only the data model model grid.

- *Each strdata namelist input can have multiple stream description files*

- *Each stream input file can contain data on a different grid*.

- *Each stream input file data is interpolated to a single model grid*. 

The strdata module will read the different streams of input data and interpolate both spatially and temporally to the appropriate final model grid and model time. 

Below is a schematic of the hierarchy:

::

   driver     :      call data land model
   data model :         data land model
   data model :           land_data               
   data model :            grid                  
   data model :           strdata                
   strdata    :    interpa   interpb   interpc     
   strdata    :    streama   streamb   streamc      
   stream     :     grida     gridb     gridc      
   stream     :   filea_01   fileb_01  filec_01   
   stream     :     ...                  ...       
   stream     :   filea_04             filec_96   

Users will primarily setup different data model configurations through existing namelist settings.
*The strdata and stream input options and format are identical for all data models*. 
The data model specific namelist has significant overlap between data models, but each data model has a slightly different set of input namelist variables and each model reads that namelist from a unique filename.
The detailed namelist options for each data model will be described later, but each model will specify a filename or filenames for strdata namelist input and each strdata namelist will specify a set of stream input files.

To continue with the above example, the following inputs would be consistent with the above figure. The data model namelist input file is hardwired to "dlnd_in" and in this case, the namelist would look something like
::

   &dlnd_nml
      decomp = '1d'
   /
   &shr_strdata_nml
     dataMode   = 'CPLHIST'
     domainFile = 'grid.nc'
     streams    = 'streama', 'streamb', 'streamc'
     mapalgo    = 'interpa', 'interpb', 'interpc'
   /

Three stream description files are then expected to be available, ``streama``, ``streamb`` and ``streamc``.
Those files specify the input data filenames, input data grids, and input fields that are expected among other things. 
The stream files are not Fortran namelist format.
Their format and options will be described later.
As an example, one of the stream description files might look like
::

   <stream>
      <dataSource>
         GENERIC
      </dataSource>
      <fieldInfo>
         <variableNames>
            dn10  dens
            slp_  pslv
            q_10  shum
            t_10  tbot
            u_10  u
            v_10  v
         </variableNames>
         <filePath>
            /glade/proj3/cseg/inputdata/atm/datm7/NYF
         </filePath>
         <offset>
            0
         </offset>
         <fileNames>
            nyf.ncep.T62.050923.nc
         </fileNames>
      </fieldInfo>
      <domainInfo>
         <variableNames>
            time   time
            lon    lon
            lat    lat
            area   area
            mask   mask
         </variableNames>
         <filePath>
            /glade/proj3/cseg/inputdata/atm/datm7/NYF
         </filePath>
         <fileNames>
            nyf.ncep.T62.050923.nc
         </fileNames>
      </domainInfo>
   </stream>


In general, these examples of input files are not complete, but they do show the general hierarchy and feel of the data model input.

-------
Summary
-------
In summary, each data model has a stream-dependent and a stream-independent namelist group. 

The stream-dependent namelist group (``shr_strdata_nml``) specifies the data model mode, stream description text files, and interpolation options. 
The stream description files will be provided as separate input files and contain the files and fields that need to be read.
The stream-independent namelist gorup contains namelist input such as the data model decomposition, etc.

From a user perspective, for any data model, it is important to know what modes are supported and the internal field names in the data model.
That information will be used in the strdata namelist and stream input files.

-------------
Next Sections
-------------
In the next sections, more details will be presented including a full description of the science modes and namelist settings for the data atmosphere, data land, data runoff, data ocean, and data ice models; namelist settings for the strdata namelist input; a description of the format and options for the stream description input files; and a list of internal field names for each of the data components.
The internal data model field names are important because they are used to setup the stream description files and to map the input data fields to the internal data model field names.


