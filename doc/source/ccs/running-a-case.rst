.. _ccs_running_a_case:

Running a Case
==============

.. contents::
   :local:

After the case has been customized, set up, and built, it is time to run it. This involves submitting the case to the batch queuing system. If a batch queuing system is not present, the case can be run interactively. The following sections provide detailed instructions on how to manage and monitor the execution of your case.

.. note:: 

    You now have the ability to create your own input data repository and add it to the **config_inputdata.xml**. This will permit you to easily collaborate by sharing your required input data with others.

Input Data
----------
All active components and data components use input data sets. In order to run CIME and the CIME-compliant active components, a local disk needs the directory tree that is specified by the XML variable ``$DIN_LOC_ROOT`` to be populated with input data.

Input data is provided by various servers configured in the model's CIME configuration. It is downloaded from the server on an as-needed basis determined by the case. Data may already exist in the default local file system's input data area as specified by ``$DIN_LOC_ROOT``.

Input data can occupy significant space on a system, so users should share a common ``$DIN_LOC_ROOT`` directory on each system if possible.

The build process will generate a list of required input data sets for each component in the ``$CASEROOT/Buildconf`` directory.

When ``case.submit`` is invoked, all of the required data sets will be checked for locally and downloaded if missing.

To check for missing data sets and download them, issue the command

::

    ./check_input_data --download

PE Layout
---------
Before you submit your job, you should ensure that the PE layout is set correctly. The PE layout is set by the XML variables **NTASKS**, **NTHRDS**, and **ROOTPE**. To see the exact settings for each component, issue the command

.. code-block:: bash

  ./pelayout

Alternatively, you can use the command

.. code-block:: bash

  ./xmlquery NTASKS,NTHRDS,ROOTPE

To change the **NTASKS** settings to 30 and the **NTHRDS** settings to 4 for all components, use the following command:

::

  ./xmlchange NTASKS=30,NTHRDS=4

To change the **NTASKS** setting for only the atmosphere component (ATM) to 8, use this command:

::

  ./xmlchange NTASKS_ATM=8

Previewing a Run
----------------
Before submitting a case, it is a good idea to preview the run to ensure that the case is set up correctly. The script ``preview_run`` will output the environment for your run along with the batch submit and mpirun commands.

.. code-block:: bash

  ./preview_run

Example output:

.. code-block:: bash

  CASE INFO:
    nodes: 8
    total tasks: 512
    tasks per node: 64
    thread count: 1
    ngpus per node: 0

  BATCH INFO:
    FOR JOB: case.run
      ENV:
        Setting Environment Albany_ROOT=/lcrc/group/e3sm/soft/albany/2024.03.26/intel/20.0.4
        Setting Environment MOAB_ROOT=/lcrc/soft/climate/moab/chrysalis/intel
        Setting Environment NETCDF_C_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/netcdf-c-4.7.4-4qjdadt
        Setting Environment NETCDF_FORTRAN_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/netcdf-fortran-4.5.3-qozrykr
        Setting Environment OMPI_MCA_sharedfp=^lockedfile,individual
        Setting Environment OMP_NUM_THREADS=1
        Setting Environment PERL5LIB=/lcrc/group/e3sm/soft/perl/chrys/lib/perl5
        Setting Environment PNETCDF_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/parallel-netcdf-1.11.0-icrpxty
        Setting Environment Trilinos_ROOT=/lcrc/group/e3sm/soft/trilinos/15.1.1/intel/20.0.4
        Setting Environment UCX_TLS=^xpmem

      SUBMIT CMD:
        sbatch --time 04:00:00 -p debug --account e3sm /gpfs/fs1/home/ac.boutte3/E3SM/cime/test1/.case.run --resubmit

      MPIRUN (job=case.run):
        srun --mpi=pmi2 -l -n 512 -N 8 --kill-on-bad-exit   --cpu_bind=cores  -c 2 -m plane=64 /lcrc/group/e3sm/ac.boutte3/scratch/chrys/test1/bld/e3sm.exe   >> e3sm.log.$LID 2>&1

    FOR JOB: case.st_archive
      ENV:
        Setting Environment Albany_ROOT=/lcrc/group/e3sm/soft/albany/2024.03.26/intel/20.0.4
        Setting Environment MOAB_ROOT=/lcrc/soft/climate/moab/chrysalis/intel
        Setting Environment NETCDF_C_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/netcdf-c-4.7.4-4qjdadt
        Setting Environment NETCDF_FORTRAN_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/netcdf-fortran-4.5.3-qozrykr
        Setting Environment OMPI_MCA_sharedfp=^lockedfile,individual
        Setting Environment OMP_NUM_THREADS=1
        Setting Environment PERL5LIB=/lcrc/group/e3sm/soft/perl/chrys/lib/perl5
        Setting Environment PNETCDF_PATH=/gpfs/fs1/soft/chrysalis/spack/opt/spack/linux-centos8-x86_64/intel-20.0.4/parallel-netcdf-1.11.0-icrpxty
        Setting Environment Trilinos_ROOT=/lcrc/group/e3sm/soft/trilinos/15.1.1/intel/20.0.4
        Setting Environment UCX_TLS=^xpmem

      SUBMIT CMD:
        sbatch --time 00:20:00 -p debug --account e3sm --dependency=afterok:0 /gpfs/fs1/home/ac.boutte3/E3SM/cime/test1/case.st_archive --resubmit

Workflow
--------
Depending on the model and case configuration, a submission may consist of multiple jobs.

There are some variables, e.g., ``JOB_WALLCLOCK_TIME``, ``JOB_QUEUE``, that can exist in multiple groups. For example, ``case.run`` and ``case.st_archive``.

To change ``JOB_WALLCLOCK_TIME`` for all groups to 2 hours, use

.. code-block:: bash

  ./xmlchange JOB_WALLCLOCK_TIME=02:00:00

To change ``JOB_WALLCLOCK_TIME`` to 20 minutes for just ``case.run``, use

.. code-block:: bash

  ./xmlchange JOB_WALLCLOCK_TIME=00:20:00 --subgroup case.run

Submitting a Case
-----------------
The script ``case.submit`` will submit your run to the batch queuing system on your machine. If you do not have a batch queuing system, ``case.submit`` will start the job interactively, given that you have a proper MPI environment defined.

.. important::

    Before submitting, ensure that ``JOB_WALLCLOCK_TIME``, ``PROJECT``, and ``QUEUE`` are set correctly.

    Running ``case.submit`` is the **ONLY** way you should start a job.

.. code-block:: bash

  ./case.submit

Output
``````
When called, the ``case.submit`` script will:

* Load the necessary environment.
* Confirm that locked files are consistent with the current XML files.
* Run ``preview_namelist``, which in turn will run each component's **cime_config/buildnml** script.
* Run :ref:`check_input_data<input_data>` to verify that the required data are present.
* Submit the job to the batch queue, which in turn will run the ``case.run`` script.

Upon successful completion of the run, ``case.run`` will:

* Put timing information in **$CASEROOT/timing**.
  See :ref:`model timing data<model-timing-data>` for details.
* Submit the short-term archiver script ``case.st_archive`` to the batch queue if ``$DOUT_S`` is TRUE. Short-term archiving will copy and move component history, log, diagnostic, and restart files from ``$RUNDIR`` to the short-term archive directory ``$DOUT_S_ROOT``.
* Resubmit ``case.run`` if ``$RESUBMIT`` > 0.

Monitoring Progress
-------------------
The ``$CASEROOT/CaseStatus`` file contains a log of all the job states and :ref:`xmlchange<ccs_xmlchange>` commands in chronological order.

Below is an example of status messages:

::

  2017-02-14 15:29:50: case.setup starting
  ---------------------------------------------------
  2017-02-14 15:29:54: case.setup success
  ---------------------------------------------------
  2017-02-14 15:30:58: xmlchange success <command> ./xmlchange STOP_N=2,STOP_OPTION=nmonths  </command>
  ---------------------------------------------------
  2017-02-14 15:31:26: xmlchange success <command> ./xmlchange STOP_N=1  </command>
  ---------------------------------------------------
  2017-02-14 15:33:51: case.build starting
  ---------------------------------------------------
  2017-02-14 15:53:34: case.build success
  ---------------------------------------------------
  2017-02-14 16:02:35: case.run starting
  ---------------------------------------------------
  2017-02-14 16:20:31: case.run success
  ---------------------------------------------------
  2017-02-14 16:20:45: st_archive starting
  ---------------------------------------------------
  2017-02-14 16:20:58: st_archive success
  ---------------------------------------------------

Troubleshooting Failures
------------------------
There are several places to look for information if a job fails.
Start with the **STDOUT** and **STDERR** file(s) in **$CASEROOT**.
If you don't find an obvious error message there, the
**$RUNDIR/$model.log.$datestamp** files will probably give you a
hint.

First, check **cpl.log.$datestamp**, which will often tell you
*when* the model failed. Then check the rest of the component log
files. See :ref:`troubleshooting run-time problems<troubleshooting>` for more information.

Starting, Stopping, and Restarting a Run
----------------------------------------
The file **env_run.xml** contains variables that may be modified at
initialization or any time during the course of a model run. Among
other features, the variables comprise coupler namelist settings for
the model stop time, restart frequency, coupler history frequency, and
a flag to determine if the run should be flagged as a continuation run.

At a minimum, you will need to set the variables ``$STOP_OPTION`` and
``$STOP_N``. Other driver namelist settings then will have consistent and
reasonable default values. The default settings guarantee that
restart files are produced at the end of the model run.

By default, the stop time settings are:

::

  STOP_OPTION = ndays
  STOP_N = 5
  STOP_DATE = -999

The default settings are appropriate only for initial testing. Before
starting a longer run, update the stop times based on the case
throughput and batch queue limits. For example, if the model runs 5
model years/day, set ``RESUBMIT=30, STOP_OPTION= nyears, and STOP_N=
5``. The model will then run in five-year increments and stop after
30 submissions.

Run-type Initialization
```````````````````````

The case initialization type is set using the ``$RUN_TYPE`` variable in
**env_run.xml**. A CIME run can be initialized in one of three ways:

startup
:::::::

In a startup run (the default), all components are initialized using
baseline states. These states are set independently by each component
and can include the use of restart files, initial files, external
observed data files, or internal initialization (that is, a "cold start").
In a startup run, the coupler sends the start date to the components
at initialization. In addition, the coupler does not need an input data file.
In a startup initialization, the ocean model does not start until the second
ocean coupling step.

branch
::::::

In a branch run, all components are initialized using a consistent
set of restart files from a previous run (determined by the
``$RUN_REFCASE`` and ``$RUN_REFDATE`` variables in **env_run.xml**).
The case name generally is changed for a branch run, but it
does not have to be. In a branch run, the ``$RUN_STARTDATE`` setting is
ignored because the model components obtain the start date from
their restart data sets. Therefore, the start date cannot be changed
for a branch run. This is the same mechanism that is used for
performing a restart run (where ``$CONTINUE_RUN`` is set to TRUE in
the **env_run.xml** file). Branch runs typically are used when
sensitivity or parameter studies are required, or when settings for
history file output streams need to be modified while still
maintaining bit-for-bit reproducibility. Under this scenario, the
new case is able to produce an exact bit-for-bit restart in the same
manner as a continuation run if no source code or component namelist
inputs are modified. All models use restart files to perform this
type of run. ``$RUN_REFCASE`` and ``$RUN_REFDATE`` are required for
branch runs. To set up a branch run, locate the restart tar file or
restart directory for ``$RUN_REFCASE`` and ``$RUN_REFDATE`` from a
previous run, then place those files in the ``$RUNDIR`` directory.
See :ref:`Starting from a reference case<starting_from_a_refcase>`.

hybrid
::::::

A hybrid run is initialized like a startup but it uses
initialization data sets from a previous case. It is similar
to a branch run with relaxed restart constraints.
A hybrid run allows users to bring together
combinations of initial/restart files from a previous case
(specified by ``$RUN_REFCASE``) at a given model output date
(specified by ``$RUN_REFDATE``). Unlike a branch run, the starting
date of a hybrid run (specified by ``$RUN_STARTDATE``) can be
modified relative to the reference case. In a hybrid run, the model
does not continue in a bit-for-bit fashion with respect to the
reference case. The resulting climate, however, should be
continuous provided that no model source code or namelists are
changed in the hybrid run. In a hybrid initialization, the ocean
model does not start until the second ocean coupling step, and the
coupler does a "cold start" without a restart file.

The variable ``$RUN_TYPE`` determines the initialization type. This
setting is only important for the initial production run when
the ``$CONTINUE_RUN`` variable is set to FALSE. After the initial
run, the ``$CONTINUE_RUN`` variable is set to TRUE, and the model
restarts exactly using input files in a case, date, and bit-for-bit
continuous fashion.

The variable ``$RUN_STARTDATE`` is the start date (in yyyy-mm-dd format)
for either a startup run or a hybrid run. If the run is targeted to be
a hybrid or branch run, you must specify values for ``$RUN_REFCASE`` and
``$RUN_REFDATE``.

Starting from a Reference Case (REFCASE)
````````````````````````````````````````
There are several XML variables that control how either a branch or a hybrid case can start up from another case.
The initial/restart files needed to start up a run from another case are required to be in ``$RUNDIR``.
The XML variable ``$GET_REFCASE`` is a flag that if set will automatically pre-stage the refcase restart data.

- If ``$GET_REFCASE`` is ``TRUE``, then the values set by ``$RUN_REFDIR``, ``$RUN_REFCASE``, ``$RUN_REFDATE``, and  ``$RUN_TOD`` are
  used to pre-stage the data by symbolic links to the appropriate path.

  The location of the necessary data to start up from another case is controlled by the XML variable ``$RUN_REFDIR``.

  - If ``$RUN_REFDIR`` is an absolute pathname, then it is expected that initial/restart files needed to start up a model run are in ``$RUN_REFDIR``.

  - If ``$RUN_REFDIR`` is a relative pathname, then it is expected that initial/restart files needed to start up a model run are in a path relative to ``$DIN_LOC_ROOT`` with the absolute pathname  ``$DIN_LOC_ROOT/$RUN_REFDIR/$RUN_REFCASE/$RUN_REFDATE``.

  - If ``$RUN_REFDIR`` is a relative pathname AND is not available in ``$DIN_LOC_ROOT``, then CIME will attempt to download the data from the input data repositories.

- If ``$GET_REFCASE`` is ``FALSE``, then the data is assumed to already exist in ``$RUNDIR``.

Restarting a Run
`````````````````
Active components (and some data components) write restart files
at intervals that are dictated by the driver via the setting of the
``$REST_OPTION`` and ``$REST_N`` variables in **env_run.xml**. Restart
files allow the model to stop and then start again with bit-for-bit
exact capability; the model output is exactly the same as if the model
had not stopped. The driver coordinates the writing of restart
files as well as the time evolution of the model.

Runs that are initialized as branch or hybrid runs require
restart/initial files from previous model runs (as specified by the
variables ``$RUN_REFCASE`` and ``$RUN_REFDATE``). Pre-stage these files
to the case ``$RUNDIR`` (normally ``$EXEROOT/../run``) before the model
run starts. Normally this is done by copying the contents of the
relevant **$RUN_REFCASE/rest/$RUN_REFDATE.00000** directory.

Whenever a component writes a restart file, it also writes a restart
pointer file in the format **rpointer.$component**. Upon a restart, each
component reads the pointer file to determine which file to read in
order to continue the run. These are examples of pointer files created
for a component set using full active model components.

::

  - rpointer.atm
  - rpointer.drv
  - rpointer.ice
  - rpointer.lnd
  - rpointer.rof
  - rpointer.cism
  - rpointer.ocn.ovf
  - rpointer.ocn.restart


If short-term archiving is turned on, the model archives the
component restart data sets and pointer files into
**$DOUT_S_ROOT/rest/yyyy-mm-dd-sssss**, where yyyy-mm-dd-sssss is the
model date at the time of the restart. (See below for more details.)

Backing up to a Previous Restart
````````````````````````````````
If a run encounters problems and crashes, you will normally have to
back up to a previous restart. If short-term archiving is enabled,
find the latest **$DOUT_S_ROOT/rest/yyyy-mm-dd-ssss/** directory
and copy its contents into your run directory (``$RUNDIR``).

Make sure that the new restart pointer files overwrite older files in
in ``$RUNDIR`` or the job may not restart in the correct place. You can
then continue the run using the new restarts.

Occasionally, when a run has problems restarting, it is because the
pointer and restart files are out of sync. The pointer files
are text files that can be edited to match the correct dates
of the restart and history files. All of the restart files should
have the same date.

Controlling Output Data
-----------------------
During a model run, each model component produces its own output
data sets in ``$RUNDIR`` consisting of history, initial, restart, diagnostics, output
log and rpointer files. Component history files and restart files are
in netCDF format. Restart files are used to either restart the same
model or to serve as initial conditions for other model cases. The
rpointer files are ascii text files that list the component history and
restart files that are required for restart.

Archiving (referred to as short-term archiving here) is the phase of a model run when output data are
moved from ``$RUNDIR`` to a local disk area (short-term archiving).
It has no impact on the production run except to clean up disk space
in the ``$RUNDIR`` which can help manage user disk quotas.

Several variables in **env_run.xml** control the behavior of
short-term archiving. This is an example of how to control the
data output flow with two variable settings:

::

  DOUT_S = TRUE
  DOUT_S_ROOT = /$SCRATCH/$user/$CASE/archive


The first setting above is the default, so short-term archiving is enabled. The second sets where to move files at the end of a successful run.

Also:

- All output data is initially written to ``$RUNDIR``.

- Unless you explicitly turn off short-term archiving, files are
  moved to ``$DOUT_S_ROOT`` at the end of a successful model run.

- Users generally should turn off short-term archiving when developing new code.

Standard output generated from each component is saved in ``$RUNDIR``
in a  *log file*. Each time the model is run, a single coordinated datestamp
is incorporated into the filename of each output log file.
The run script generates the datestamp in the form YYMMDD-hhmmss, indicating
the year, month, day, hour, minute and second that the run began
(ocn.log.040526-082714, for example).

By default, each component also periodically writes history files
(usually monthly) in netCDF format and also writes netCDF or binary
restart files in the ``$RUNDIR`` directory. The history and log files
are controlled independently by each component. History output control
(for example, output fields and frequency) is set in each component's namelists.

The raw history data does not lend itself well to easy time-series
analysis. For example, CAM writes one or more large netCDF history
file(s) at each requested output period. While this behavior is
optimal for model execution, it makes it difficult to analyze time
series of individual variables without having to access the entire
data volume. Thus, the raw data from major model integrations usually
is post-processed into more user-friendly configurations, such as
single files containing long time-series of each output fields, and
made available to the community.

The output data flow from a successful run depends on whether or not
short-term archiving is enabled, as it is by default.

No Archiving
````````````
If no short-term archiving is performed, model output data remains
remain in the run directory as specified by ``$RUNDIR``.

Short-term Archiving
````````````````````
If short-term archiving is enabled, component output files are moved
to the short-term archiving area on local disk, as specified by
``$DOUT_S_ROOT``. The directory normally is **$EXEROOT/../../archive/$CASE.**
and has the following directory structure: ::

   rest/yyyy-mm-dd-sssss/
   logs/
   atm/hist/
   cpl/hist
   glc/hist
   ice/hist
   lnd/hist
   ocn/hist
   rof/hist
   wav/hist
   ....

The **logs/** subdirectory contains component log files that were
created during the run. Log files are also copied to the short-term
archiving directory and therefore are available for long-term archiving.

The **rest/** subdirectory contains a subset of directories that each contains
a *consistent* set of restart files, initial files and rpointer
files. Each subdirectory has a unique name corresponding to the model
year, month, day and seconds into the day when the files were created.
The contents of any restart directory can be used to create a branch run
or a hybrid run or to back up to a previous restart date.

Long-term Archiving
```````````````````
Users may choose to follow their institution's preferred method for long-term
archiving of model output. Previous releases of CESM provided an external
long-term archiver tool that supported mass tape storage and HPSS systems.
However, with the industry migration away from tape archives, it is no longer
feasible for CIME to support all the possible archival schemes available.

Pre and Post Processing
-----------------------
CIME provides a capability to run a task on the compute nodes either
before or after the model run.  CIME also provides a data assimilation
capability which will cycle the model and then a user defined task for
a user determined number of cycles.

Scripts
```````
Variables ``PRERUN_SCRIPT`` and ``POSTRUN_SCRIPT`` can each be used to name
a script which should be executed immediately prior starting or
following completion of the CESM executable within the batch
environment.  The script is expected to be found in the case directory
and will receive one argument which is the full path to that
directory.  If the script is written in python and contains a
subroutine with the same name as the script, it will be called as a
subroutine rather than as an external shell script.

CIME provides the ability to execute user-defined scripts during
the execution of ``case.run``. These user-defined scripts can be
invoked either before and/or after the model is run. The xml variables that controls this capability are:

* ``PRERUN_SCRIPT``: points to an external script to be run before model execution.

* ``POSTRUN_SCRIPT``: points to an external script to be run after successful model completion.

.. note::
  
  When these scripts are called, the full processor allocation for the job will be used - even if only 1 processor actually is invoked for the external script.

Data Assimilation Scripts
`````````````````````````
Variables ``DATA_ASSIMILATION``, ``DATA_ASSIMILATION_SCRIPT``, and
``DATA_ASSIMILATION_CYCLES`` may also be used to externally control
model evolution.  If ``DATA_ASSIMILATION`` is true after the model
completes the ``DATA_ASSIMILATION_SCRIPT`` will be run and then the
model will be started again ``DATA_ASSIMILATION_CYCLES`` times.  The
script is expected to be found in the case directory and will receive
two arguments, the full path to that directory and the cycle number.
If the script is written in python and contains a subroutine with the
same name as the script, it will be called as a subroutine rather than
as an external shell script.

A simple example pre run script.

::

   #!/usr/bin/env python3
   import sys
   from CIME.case import Case

   def myprerun(caseroot):
       with Case(caseroot) as case:
            print ("rundir is ",case.get_value("RUNDIR"))

    if __name__ == "__main__":
      caseroot = sys.argv[1]
      myprerun(caseroot)

CIME provides the ability to hook in a data assimilation utility via a set of xml variables:

.. list-table:: Data Assimilation Variables
  :widths: 20 80
  :header-rows: 1

  * - Variable
    - Description
  * - DATA_ASSIMILATION_SCRIPT
    - Points to an external script to be run **after** model completion.
  * - DATA_ASSIMILATION_CYCLES
    - Integer that controls the number of data assimilation cycles. The run script will loop over these number of data assimilation cycles and for each cycle will run the model and subsequently run the data assimilation script.
  * - DATA_ASSIMILATION
    - If set to TRUE for a given component, then a resume signal will be sent to that component at initialization. If set, the component will execute special post data assimilation logic on initialization. See the component documentation for details. This flag is a bit subtle in that it is a per-component flag, not a model wide flag.

The following will show which components have data assimilation enabled.

.. code-block:: bash

  ./xmlquery DATA_ASSIMILATION

The output may look like this

.. code-block:: bash
  
  DATA_ASSIMILATION: ['CPL:FALSE', 'ATM:FALSE', 'LND:FALSE', 'ICE:FALSE', 'OCN:FALSE', 'ROF:FALSE', 'GLC:FALSE', 'WAV:FALSE', 'IAC:FALSE']

This can be set for a single component.

.. code-block:: bash

  ./xmlchange DATA_ASSIMILATION_LND=TRUE