.. _running-a-case:

***************
Running a Case
***************

.. _case-submit:

========================
Calling **case.submit**
========================

Before you submit the case using case.submit, you need to make sure
the batch queue variables are set correctly for the specific run being
targeted.  The batch submissions variables are contained in the file
``$CASEROOT/env_batch.xml`` under the XML ``<group id="case.run">``
and ``<group id="case.st_archive">`` elements. Make sure that you
have appropriate account numbers (``PROJECT``), time limits
(``JOB_WALLCLOCK_TIME``), and queue (``JOB_QUEUE``) for those groups..

You should also modify ``$CASEROOT/env_run.xml`` for
your particular needs using :ref:`xmlchange<modifying-an-xml-file>`.

Once you have run **case.setup** and **case.build**, you need to run
**case.submit** to submit the run to your machine's batch queue
system.
::

   > cd $CASEROOT
   > ./case.submit

---------------------------------
Result of running case.submit
---------------------------------

When called, the script, ``case.submit`` will:

- Load the necessary environment.

- Check that locked files (in ``$CASEROOT/LockedFiles``) are consistent with the current xml files.

- Run **preview_namelist** which in turn will run each component's **buildnml**

- Run :ref:`**check_input_data**<input_data>` to verify that the required input data for the case is present on local disk in ``$DIN_LOC_ROOT``.

- Submit the job to the batch queue which in turn will run the ``$CASEROOT`` script **case.run**.

Upon successful completion of the run, **case.run** will:

- Put timing information in ``$CASEROOT/timing``. A summary timing
  output file is produced after every model run. This file is
  ``$CASEROOT/timing/ccsm_timing.$CASE.$date.gz`` (where ``$date`` is
  a datestamp set by CIME at runtime) and contains a summary of
  various information. See :ref:`model timing data<model-timing-data>`
  for more details.

- Copy log files back to ``$LOGDIR``.

- Submit the short term archiver script **case.st_archive** to the batch queue if ``$DOUT_S`` is TRUE.

- Resubmit **case.run** if ``$RESUBMIT`` >0.  

Short term archiving will copy and move component history, log,
diagnostic, and restart files from ``$RUNDIR`` to the short-term
archive directory, ``$DOUT_S_ROOT``.

---------------------------------
Monitoring case job statuses
---------------------------------

The ``$CASEROOT/CaseStatus`` file contains a log of all the job states 
and xmlchange commands in chronological order. An example of status
messages from a CaseStatus file with successful job completions 
includes:
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

After the short term archiver completes, data from the ``$RUNDIR`` is in the
subdirectories under ``$DOUT_S_ROOT``. 

.. note:: 
  Once you have a successful first run, you must set the
  ``env_run.xml`` variable ``$CONTINUE_RUN`` to ``TRUE`` in
  ``env_run.xml`` before resubmitting, otherwise the job will not
  progress. You may also need to modify the ``env_run.xml`` variables
  ``$STOP_OPTION``, ``$STOP_N`` and/or ``$STOP_DATE`` as well as
  ``$REST_OPTION``, ``$REST_N`` and/or ``$REST_DATE``, and ``$RESUBMIT``
  before resubmitting.

You can see a complete example of how to run a case in :ref:`the basic example<faq-basic-example>`.

---------------------------------
Troubleshooting a job that fails
---------------------------------

There are several places where you should look for information if a
job fails. Start with the STDOUT and STDERR file(s) in ``$CASEROOT``.
If you don't find an obvious error message there, the
$RUNDIR/$model.log.$datestamp files will probably give you a
hint. First check cpl.log.$datestamp, because it will often tell you
when the model failed. Then check the rest of the component log
files. Please see :ref:`troubleshooting run-time
problems<troubleshooting>` for more information.

.. _input_data:

====================================================
Input data
====================================================

The ``$CASEROOT`` script **check_input_data** determines if the
required data files for your case exist on local disk in the
appropriate subdirectory of ``$DIN_LOC_ROOT``.  As part of submitting
the run to the batch queueing system, **case.submit** also calls
**check_input_data** to verify that required input data sets are
accessible on local disk and download missing data automatically to
local disk from in the appropriate subdirectory of ``$DIN_LOC_ROOT``

The required input datasets needed for each component are found in the
``$CASEROOT/Buildconf`` directory in the files
``xxx.input_data_list``, where ``xxx`` is the component name.
These files are generated via a call to **preview_namlists** and are in
turn created by each component's **buildnml** script.  As an example,
for compsets consisting only of data models (i.e. ``A`` compsets),
the following files will be created in ``$CASEROOT/Buildconf`` when
**case.submit** is called: 
::

   datm.input_data_list
   dice.input_data_list
   docn.input_data_list
   drof.input_data_list

**check_input_data** verifies that each file listed in the
``xxx.input_data_list`` files exists in ``$DIN_LOC_ROOT``.  If any of
the required datasets do not exist locally, **check_input_data**
provides the capability for downloading them to the ``$DIN_LOC_ROOT``
directory hierarchy via interaction with the Subversion input data server.  You
can independently verify that the required data is present locally by
using the following commands: 
::

   > cd $CASEROOT
   > check_input_data -help
   > check_input_data -inputdata $DIN_LOC_ROOT -check

If input data sets are missing, you must obtain the datasets from the input data server:
::

   > cd $CASEROOT
   > check_input_data -inputdata $DIN_LOC_ROOT -export

Required data files not on local disk will be downloaded through
interaction with the Subversion input data server.  These will be
placed in the appropriate subdirectory of ``$DIN_LOC_ROOT``.

.. _controlling-start-stop-restart:

====================================================
Controlling starting, stopping and restarting a run
====================================================

``env_run.xml`` contains variables which may be modified at
initialization and any time during the course of the model run.
Among other features, the ``env_run.xml`` file variables comprise
coupler namelist settings for the model stop time, model restart
frequency, coupler history frequency and a flag to determine if the
run should be flagged as a continuation run.  At a minimum, you will
only need to set the variables ``$STOP_OPTION`` and ``$STOP_N``.  The
other driver namelist settings will then be given consistent and
reasonable default values.  These default settings guarantee that
restart files are produced at the end of the model run.

---------------------------------------------------
Run-type initialization
---------------------------------------------------

The case initialization type is set using the ``$RUN_TYPE`` variable in
``env_run.xml``. A CIME run can be initialized in one of three ways;
startup, branch, or hybrid.

``startup``
  In a startup run (the default), all components are initialized using
  baseline states.  These baseline states are set independently by
  each component and can include the use of restart files, initial
  files, external observed data files, or internal initialization
  (i.e., a "cold start").  In a startup run, the coupler sends the
  start date to the components at initialization. In addition, the
  coupler does not need an input data file. In a startup
  initialization, the ocean model does not start until the second
  ocean coupling step.

``branch``
  In a branch run, all components are initialized using a consistent
  set of restart files from a previous run (determined by the
  ``$RUN_REFCASE`` and ``$RUN_REFDATE`` variables in ``env_run.xml``).
  The case name is generally changed for a branch run, although it
  does not have to be.  In a branch run, setting ``$RUN_STARTDATE`` is
  ignored because the model components obtain the start date from
  their restart datasets.  Therefore, the start date cannot be changed
  for a branch run.  This is the same mechanism that is used for
  performing a restart run (where ``$CONTINUE_RUN`` is set to TRUE in
  the ``env_run.xml`` file).  Branch runs are typically used when
  sensitivity or parameter studies are required, or when settings for
  history file output streams need to be modified while still
  maintaining bit-for-bit reproducibility.  Under this scenario, the
  new case is able to produce an exact bit-for-bit restart in the same
  manner as a continuation run if no source code or component namelist
  inputs are modified.  All models use restart files to perform this
  type of run. ``$RUN_REFCASE`` and ``$RUN_REFDATE`` are required for
  branch runs.  To set up a branch run, locate the restart tar file or
  restart directory for ``$RUN_REFCASE`` and ``$RUN_REFDATE`` from a
  previous run, then place those files in the ``$RUNDIR``
  directory. See :ref:`setting up a branch
  run<setting-up-a-branch-run>`.

``hybrid``
  A hybrid run indicates that the model is initialized more like a
  startup, but uses initialization datasets from a previous case.
  This is somewhat analogous to a branch run with relaxed restart
  constraints.  A hybrid run allows users to bring together
  combinations of initial/restart files from a previous case
  (specified by ``$RUN_REFCASE``) at a given model output date
  (specified by ``$RUN_REFDATE``).  Unlike a branch run, the starting
  date of a hybrid run (specified by ``$RUN_STARTDATE``) can be
  modified relative to the reference case.  In a hybrid run, the model
  does not continue in a bit-for-bit fashion with respect to the
  reference case.  The resulting climate, however, should be
  continuous provided that no model source code or namelists are
  changed in the hybrid run.  In a hybrid initialization, the ocean
  model does not start until the second ocean coupling step, and the
  coupler does a "cold start" without a restart file.

The variable ``$RUN_TYPE`` determines the initialization type.  This
setting is only important for the initial run of a production run when
the ``$CONTINUE_RUN`` variable is set to FALSE.  After the initial
run, the ``$CONTINUE_RUN`` variable is set to TRUE, and the model
restarts exactly using input files in a case, date, and bit-for-bit
continuous fashion.  

The variable ``$RUN_STARTDATE`` is the start date
(in yyyy-mm-dd format) for either a startup or hybrid run.  If the run is
targeted to be a hybrid or branch run, you must also specify values
for ``$RUN_REFCASE`` and ``$RUN_REFDATE``.  All run startup variables
are discussed in `run start control variables
<http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

A brief note on restarting runs; when you first begin a branch, hybrid
or startup run, ``CONTINUE_RUN`` must be set to ``FALSE``.  After the
job has successfully run and there are restart files, you will need to
change ``CONTINUE_RUN`` to TRUE for the remainder of your run.
Setting the ``RESUBMIT`` option to a value > 0 will cause the
``CONTINUE_RUN`` variable to be automatically set to ``TRUE`` upon
completion of the initial run.

By default,
::

  STOP_OPTION = ndays
  STOP_N = 5
  STOP_DATE = -999

The default setting is only appropriate for initial testing. Before a
longer run is started, update the stop times based on the case
throughput and batch queue limits. For example, if the model runs 5
model years/day, set ``RESUBMIT=30, STOP_OPTION= nyears, and STOP_N=
5``. The model will then run in five year increments, and stop after
30 submissions.

.. _controlling-output-data:

=========================
Controlling output data
=========================

During a model run, each model component produces its own output
datasets consisting of history, initial, restart, diagnostics, output
log and rpointer files. Component history files and restart files are
in netCDF format. Restart files are used to either exactly restart the
model or to serve as initial conditions for other model cases. The
rpointer files are text files listing the required component history
and restart files required for restart. 

Archiving is a phase of a model run where the generated output data is
moved from ``$RUNDIR`` to a local disk area (short-term archiving).
It has no impact on the production run except to clean up disk space
in the ``$RUNDIR`` and help manage user quotas. 

In ``env_run.xml``, several variables control the behavior of
short-term archiving. As an example for controlling the data output
flow using the following example settings: 
::

  DOUT_S = TRUE
  DOUT_S_ROOT = /$SCRATCH/$user/$CASE/archive


Several important points need to be made about short term archiving:

- By default, short-term archiving is enabled (``$DOUT_S = TRUE``)

- All output data is initially written to ``$RUNDIR``.

- Unless a user explicitly turns off short-term archiving, files will
  be moved to ``$DOUT_S_ROOT`` at the end of a successful model run.

- Users should generally turn off short-term archiving when developing new code.

Standard output generated from each component is saved in a "log file"
for each component in the ``$RUNDIR``. Each time the model is run, a
single coordinated datestamp is incorporated in the filenames of all
output log files associated with that run. This common datestamp is
generated by the run script and is of the form YYMMDD-hhmmss, where
YYMMDD are the Year, Month, Day and hhmmss are the hour, minute and
second that the run began (e.g. ocn.log.040526-082714). Log files are
also copied to a user specified directory using the variable
``$LOGDIR`` in ``env_run.xml``. The default is a 'logs' subdirectory
in the ``$CASEROOT`` directory.

By default, each component also periodically writes history files
(usually monthly) in netCDF format and also writes netCDF or binary
restart files in the ``$RUNDIR`` directory. The history and log files
are controlled independently by each component. History output control
(i.e. output fields and frequency) is set in the
``Buildconf/$component.buildnml.csh`` files.

The raw history data does not lend itself well to easy time-series
analysis. For example, CAM writes one or more large netCDF history
file(s) at each requested output period. While this behavior is
optimal for model execution, it makes it difficult to analyze time
series of individual variables without having to access the entire
data volume. Thus, the raw data from major model integrations is
usually postprocessed into more user-friendly configurations, such as
single files containing long time-series of each output fields, and
made available to the community.

For CESM, please refer to the `CESM2 Output Filename Conventions 
<http://www.cesm.ucar.edu/models/cesm2.0/cesm/filename_conventions_cesm.html>`_
for a description of output data filenames. 

.. _restarting-a-run:

======================
Restarting a run
======================

Restart files are written by each active component (and some data
components) at intervals dictated by the driver via the setting of the
``env_run.xml`` variables, ``$REST_OPTION`` and ``$REST_N``. Restart
files allow the model to stop and then start again with bit-for-bit
exact capability (i.e. the model output is exactly the same as if it
had never been stopped). The driver coordinates the writing of restart
files as well as the time evolution of the model. All components
receive restart and stop information from the driver and write
restarts or stop as specified by the driver.

It is important to note that runs that are initialized as branch or
hybrid runs, will require restart/initial files from previous model
runs (as specified by the variables, ``$RUN_REFCASE`` and
``$RUN_REFDATE``). These required files must be prestaged by the user
to the case ``$RUNDIR`` (normally ``$EXEROOT/run``) before the model
run starts. This is normally done by just copying the contents of the
relevant ``$RUN_REFCASE/rest/$RUN_REFDATE.00000`` directory.

Whenever a component writes a restart file, it also writes a restart
pointer file of the form, ``rpointer.$component``. The restart pointer
file contains the restart filename that was just written by the
component. Upon a restart, each component reads its restart pointer
file to determine the filename(s) to read in order to continue the
model run. As examples, the following pointer files will be created
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


If short-term archiving is turned on, then the model archives the
component restart datasets and pointer files into
``$DOUT_S_ROOT/rest/yyyy-mm-dd-sssss``, where yyyy-mm-dd-sssss is the
model date at the time of the restart (see `below for more details
<http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). 

---------------------------------
Backing up to a previous restart
---------------------------------

If a run encounters problems and crashes, you will normally have to
back up to a previous restart. Assuming that short-term archiving is
enabled, you will need to find the latest
``$DOUT_S_ROOT/rest/yyyy-mm-dd-ssss/`` directory that was created and
copy the contents of that directory into your run directory
(``$RUNDIR``). You can then continue the run and these restarts will
be used. It is important to make sure the new rpointer.* files
overwrite the rpointer.* files that were in ``$RUNDIR``, or the job
may not restart in the correct place.

Occasionally, when a run has problems restarting, it is because the
rpointer files are out of sync with the restart files. The rpointer
files are text files and can easily be edited to match the correct
dates of the restart and history files. All the restart files should
have the same date.

============================
Archiving model output data
============================

All component log files are copied to the directory specified by the
``env_run.xml`` variable ``$LOGDIR`` which by default is set to
``$CASEROOT/logs``. This location is where log files are copied when
the job completes successfully. If the job aborts, the log files will
NOT be copied out of the ``$RUNDIR`` directory.

Once a model run has completed successfully, the output data flow will
depend on whether or not short-term archiving is enabled (as set by
the ``env_run.xml`` variable, ``$DOUT_S``). By default, short-term
archiving will be done (``DOUT_S=TRUE``).

-------------
No archiving
-------------

If no short-term archiving is performed, then all model output data
will remain in the run directory, as specified by the ``env_run.xml``
variable, ``$RUNDIR``. 

---------------------
Short-term archiving
---------------------

If short-term archiving is enabled, the component output files will be
moved to the short term archiving area on local disk, as specified by
``$DOUT_S_ROOT``. The directory ``DOUT_S_ROOT`` is normally set to
``$EXEROOT/../archive/$CASE.`` and will contain the following
directory structure: ::

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

logs/ contains component log files created during the run. In addition
to ``$LOGDIR``, log files are also copied to the short-term archiving
directory and therefore are available for long-term archiving.

rest/ contains a subset of directories that each contain a
*consistent* set of restart files, initial files and rpointer
files. Each sub-directory has a unique name corresponding to the model
year, month, day and seconds into the day where the files were created
(e.g. 1852-01-01-00000/). The contents of any restart directory can be
used to create a branch run or a hybrid run or back up to a previous
restart date.

---------------------
Long-term archiving
---------------------

Users may choose to user their institution's preferred method for long-term 
archiving of model output. Previous releases of CESM provided an external
long-term archiver tool which supported mass tape storage and HPSS systems.
However, with the industry migration away from tape archives, it is no longer
feasible for CIME to support all the possible archival schemes available. 

