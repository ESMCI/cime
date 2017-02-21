.. _design-details:

================
 Design Details
================

The data model functionality is executed via set of specific operations associated with reading and interpolating data in space and time. 
The strdata implementation does the following:

1. determines nearest lower and upper bound data from the input dataset 
2. if that is new data then read lower and upper bound data
3. fill lower and upper bound data
4. spatially map lower and upper bound data to model grid
5. time interpolate lower and upper bound data to model time
6. return fields to data model


.. _io-details:

---------------------
IO Through Data Models
----------------------

Namlist variables referenced below are discussed in detail in :ref:`stream data namelist section <shr-strdata-nml>`.

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
.. _restart-files:

-------------
Restart Files
-------------
Restart files are generated automatically by the data models based upon a flag sent from the driver.
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


