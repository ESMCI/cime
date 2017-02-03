.. _running-a-case:

Running a Case
========================

To run a CIME case, you will run the script ``case.submit`` after you have modified ``env_run.xml`` for your particular needs.

The `env_run.xml <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ file contains variables which may be modified at the initialization of a model run and during the course of that model run. These variables comprise coupler namelist settings for the model stop time, model restart frequency, coupler history frequency and a flag to determine if the run should be flagged as a continuation run. In general, you only need to set the variables ``$STOP_OPTION`` and ``$STOP_N``. The other coupler settings will then be given consistent and reasonable default values. These default settings guarantee that restart files are produced at the end of the model run.

In the following, we focus on the handling of run control (e.g. length of run, continuing a run) and output data. We also give a more detailed description of CIME restarts.

Controlling starting, stopping and restarting a run
---------------------------------------------------

The case initialization type is set in ``env_run.xml``. A CIME run can be initialized in one of three ways; startup, branch, or hybrid.

startup
  In a startup run (the default), all components are initialized using baseline states. These baseline states are set independently by each component and can include the use of restart files, initial files, external observed data files, or internal initialization (i.e., a "cold start"). In a startup run, the coupler sends the start date to the components at initialization. In addition, the coupler does not need an input data file. In a startup initialization, the ocean model does not start until the second ocean coupling step.

branch
  In a branch run, all components are initialized using a consistent set of restart files from a previous run (determined by the ``$RUN_REFCASE`` and ``$RUN_REFDATE`` variables in ``env_run.xml``). The case name is generally changed for a branch run, although it does not have to be. In a branch run, setting ``$RUN_STARTDATE`` is ignored because the model components obtain the start date from their restart datasets. Therefore, the start date cannot be changed for a branch run. This is the same mechanism that is used for performing a restart run (where ``$CONTINUE_RUN`` is set to TRUE in the ``env_run.xml`` file).

  Branch runs are typically used when sensitivity or parameter studies are required, or when settings for history file output streams need to be modified while still maintaining bit-for-bit reproducibility. Under this scenario, the new case is able to produce an exact bit-for-bit restart in the same manner as a continuation run if no source code or component namelist inputs are modified. All models use restart files to perform this type of run. ``$RUN_REFCASE`` and ``$RUN_REFDATE`` are required for branch runs.

  To set up a branch run, locate the restart tar file or restart directory for ``$RUN_REFCASE`` and ``$RUN_REFDATE`` from a previous run, then place those files in the ``$RUNDIR`` directory. See `setting up a branch run <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for an example.

hybrid
  A hybrid run indicates that the model is initialized more like a startup, but uses initialization datasets from a previous case. 
  This is somewhat analogous to a branch run with relaxed restart constraints. 
  A hybrid run allows users to bring together combinations of initial/restart files from a previous case (specified by ``$RUN_REFCASE``) at a given model output date (specified by ``$RUN_REFDATE``). 
  Unlike a branch run, the starting date of a hybrid run (specified by ``$RUN_STARTDATE``) can be modified relative to the reference case. 
  In a hybrid run, the model does not continue in a bit-for-bit fashion with respect to the reference case. 
  The resulting climate, however, should be continuous provided that no model source code or namelists are changed in the hybrid run. 
  In a hybrid initialization, the ocean model does not start until the second ocean coupling step, and the coupler does a "cold start" without a restart file.

The variable ``$RUN_TYPE`` determines the initialization type. This setting is only important for the initial run of a production run when the $CONTINUE_RUN variable is set to FALSE. After the initial run, the ``$CONTINUE_RUN`` variable is set to TRUE, and the model restarts exactly using input files in a case, date, and bit-for-bit continuous fashion. The variable ``$RUN_TYPE`` is the start date (in yyyy-mm-dd format) either a startup or hybrid run. If the run is targeted to be a hybrid or branch run, you must also specify values for ``$RUN_REFCASE`` and ``$RUN_REFDATE``. All run startup variables are discussed in `run start control variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

Before a job is submitted to the batch system, you need to first check that the batch submission lines in ``env_batch.xml`` are appropriate. These lines should be checked and modified accordingly for appropriate account numbers, time limits, and stdout/stderr file names. You should then modify ``env_run.xml`` to determine the key run-time settings. See `controlling run termination <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `controlling run restarts <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, and `performing model restarts <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for more details. A brief note on restarting runs. When you first begin a branch, hybrid or startup run, CONTINUE_RUN must be set to FALSE. When you successfully run and get a restart file, you will need to change CONTINUE_RUN to TRUE for the remainder of your run. See performing model restarts for more details.   Setting the RESUBMIT option to a value > 0 will cause the CONTINUE_RUN variable to be automatically set to TRUE upon completion of the initial run.

By default,
```
STOP_OPTION = ndays
STOP_N = 5
STOP_DATE = -999
```
The default setting is only appropriate for initial testing. Before a longer run is started, update the stop times based on the case throughput and batch queue limits. For example, if the model runs 5 model years/day, set ``RESUBMIT=30, STOP_OPTION= nyears, and STOP_N= 5``. The model will then run in five year increments, and stop after 30 submissions.

Customizing component-specific namelist settings
------------------------------------------------

All CIME_compliant components generate their namelist settings using the ``cime_config/buildnml`` file located in the component's directory tree.
As an example, the CIME data atmosphere model (DATM), generates namelists using the script ``$CIMEROOT/components/data_comps/datm/cime_config/buildnml``.

**User specific component namelist changes should only be made only by editing the ``$CASEROOT/user_nl_xxx`` files OR by changing xml variables in `env_run.xml` or `env_build.xml`**. 
A full discussion of how to change the namelist variables for each component is provided below. 
You can preview the ``$CASEROOT`` component namelists by running ``preview_namelists`` from your ``$CASEROOT``. 
Calling ``review_namelists`` results in the creation of component namelists (e.g. atm_in, lnd_in, .etc) in ``$CASEROOT/CaseDocs/``. 
The namelist files created in the ``CaseDocs/`` are there only for user reference and SHOULD NOT BE EDITED since they are overwritten every time ``preview_namelists``, ``case.submit`` and ``case.build`` are called. 
A complete documentation of all `CESM2 model component namelists <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
The only files that you should modify are in ``$CASEROOT``. 
The following represents a summary of controlling and modifying component-specific run-time settings:

DRV
^^^
Driver namelist variables belong in two groups - those that are set directly from ``$CASEROOT` xml variables and those that are set by the driver ``buildnml`` utility (``$CIMEROOT/driver_cpl/cime_config/buildnml``).
All driver namelist variables are defined in ``$CIMEROOT/driver_cpl/cime_config/namelist_definition_drv.xml``. 
Those variables that can only be changed by modifying xml variables appear with the ``entry`` attribute ``modify_via_xml="xml_variable_name"``.
All other variables that appear ``$CIMEROOT/driver_cpl/cime_config/namelist_definition_drv.xml`` can be modified by adding a key-word value pair at the end of ``user_nl_cpl``.
For example, to change the driver namelist value of ``eps_frac`` to ``1.0e-15``, you should add the following line to the end of the ``user_nl_cpl``
::

   eps_frac = 1.0e-15

To see the result of this modification to ``user_nl_cpl`` call ``preview_namelists`` and verify that this new value appears in ``CaseDocs/drv_in``.

DATM
^^^^
DATM is discussed in detail in `Data Model's User's Guide <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
DATM is normally used to provide observational forcing data (or forcing data produced by a previous run using active components) to drive CLM (I compset), POP2 (C compset), and POP2/CICE (G compset). 
As a result, DATM variable settings are specific to the compset that will be targeted.

DATM can be user configured in three different ways.

You can set `DATM run-time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ my modifying control settings for CLM and CPLHIST forcing.

You can edit ``user_nl_datm`` to change namelist settings namelists settings by adding all user specific namelist changes in the form of "namelist_var = new_namelist_value". 
Note that any namelist variable from shr_strdata_nml and datm_nml can be modified below using the this syntax. 
Use preview_namelists to view (not modify) the output namelist in ``CaseDocs``.

You can modify the contents of a DATM stream txt file. To do this:

- use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs``

- place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended

- **Make sure you change the permissions of the file to be writeable** (chmod 644)

- Modify the ``user_datm.streams.txt.*`` file.

As an example, if the stream txt file in ``CaseDocs/`` is datm.streams.txt.CORE2_NYF.GISS, the modified copy in ``$CASEROOT`` should be ``user_datm.streams.txt.CORE2_NYF.GISS``. After calling **preview_namelists** again, you should see your new modifications appear in ``CaseDocs/datm.streams.txt.CORE2_NYF.GISS``.

DOCN
^^^^
DOCN is discussed in detail in `Data Model's User's Guide <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

DOCN running in prescribed mode assumes that the only field in the input stream is SST and also that SST is in Celsius and must be converted to Kelvin. 
All other fields are set to zero except for ocean salinity, which is set to a constant reference salinity value. 
Normally the ice fraction data (used for prescribed CICE) is found in the same data files that provide SST data to the data ocean model since SST and ice fraction data are derived from the same observational data sets and are consistent with each other. 
For DOCN prescribed mode, default yearly climatological datasets are provided for various model resolutions. 
For multi-year runs requiring AMIP datasets of sst/ice_cov fields, you need to set the variables for `DOCN_SSTDATA_FILENAME, DOCN_SSTDATA_YEAR_START, and DOCN_SSTDATA_YEAR_END <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
CICE in prescribed mode also uses these values.

DOCN running as a slab ocean model is used (in conjunction with CICE running in prognostic mode) in all `E compsets <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
SOM ("slab ocean model") mode is a prognostic mode. 
This mode computes a prognostic sea surface temperature and a freeze/melt potential (surface Q-flux) used by the sea ice model. 
This calculation requires an external SOM forcing data file that includes ocean mixed layer depths and bottom-of-the-slab Q-fluxes. 
Scientifically appropriate bottom-of-the-slab Q-fluxes are normally ocean resolution dependent and are derived from the ocean model output of a fully coupled run. 
Note that while this mode runs out of the box, the default SOM forcing file is not scientifically appropriate and is provided for testing and development purposes only. 
Users must create scientifically appropriate data for their particular application. A tool is available to derive valid SOM forcing.

DOCN can be user-customized in three ways.

You can set `DOCN run-time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

You can edit ``user_nl_docn`` to change namelist settings by adding all user specific namelist changes in the form of "namelist_var = new_namelist_value". 
Note that any namelist variable from shr_strdata_nml and datm_nml can be modified below using the this syntax. 
Use **preview_namelists** to view (not modify) the output namelist in ``CaseDocs``.

You can modify the contents of a DOCN stream txt file. 
To do this:

- use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``

- place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended

- **Make sure you change the permissions of the file to be writeable** (chmod 644)

- Modify the ``user_docn.streams.txt.*`` file.

As an example, if the stream text file in ``CaseDocs/`` is 
``doc.stream.txt.prescribed``, the modified copy in ``$CASEROOT`` should be ``user_docn.streams.txt.prescribed``. 
After changing this file and calling **preview_namelists** again, you should see your new modifications appear in ``CaseDocs/docn.streams.txt.prescribed``.

DICE
^^^^
DICE is discussed in detail in `Data Model's User's Guide <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

DICE can be user-customized in three ways.

You can set `DICE run-time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

You can edit ``user_nl_dice`` to change namelist settings by adding all user specific namelist changes in the form of "namelist_var = new_namelist_value". Note that any namelist variable from shr_strdata_nml and datm_nml can be modified below using the this syntax. Use **preview_namelists** to view (not modify) the output namelist in ``CaseDocs/``.

You can modify the contents of a DICE stream txt file. To do this:

- use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``

- place a *copy* of this file in ``$CASEROOT`` with the string "*user*_" prepended

- **Make sure you change the permissions of the file to be writeable** (chmod 644)

- Modify the ``user_dice.streams.txt.*`` file.

DLND
^^^^
DLND is discussed in detail in `Data Model's User's Guide <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. The data land model is different from the other data models because it can run as a purely data-land model (reading in coupler history data for atm/land fluxes and land albedos produced by a previous run), or to read in model output from CLM to send to CISM.

DLND can be user-customized in three ways:

You can set `DLND run-time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

You can edit ``user_nl_dlnd`` OR ``user_nl_dsno`` depending on the component set, to change namelist settings namelists settings by adding all user specific namelist changes in the form of "namelist_var = new_namelist_value". Note that any namelist variable from ``shr_strdata_nml`` and ``dlnd_nml`` or ``dsno_nml`` can be modified below using the this syntax. Use **preview_namelists** to view (not modify) the output namelist in ``CaseDocs/``.

You can modify the contents of a DLND stream txt file. To do this:

- use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``

- place a *copy* of this file in ``$CASEROOT`` with the string "*user*_" prepended

- **Make sure you change the permissions of the file to be writeable** (chmod 644)

- Modify the ``user_dlnd.streams.txt.*`` file.

DROF
^^^^
DROF is discussed in `Data Model's User's Guide <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. The data river runoff model reads in runoff data and sends it back to the coupler. In general, the data river runoff model is only used to provide runoff forcing data to POP2 when running C or G compsets

DROF can be user-customized in three ways:

You can set `DROF run-time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

You can edit ``user_nl_drof`` to change namelist settings namelists settings by adding all user specific namelist changes in the form of "namelist_var = new_namelist_value". Note that any namelist variable from ``shr_strdata_nml`` and ``drof_nml`` can be modified using the this syntax. Use **preview_namelists** to view (not modify) the output namelist in ``CaseDocs/``.

You can modify the contents of a DROF stream txt file. To do this:

- use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``

- place a *copy* of this file in ``$CASEROOT`` with the string "*user*_" prepended

- **Make sure you change the permissions of the file to be writeable** (chmod 644)

- Modify the ``user_drof.streams.txt.*`` file.

Customizing CESM prognostic component-specific namelist settings
----------------------------------------------------------------

CAM
^^^
CAM's `configure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `build-namelist <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ utilities are called by ``Buildconf/cam.buildnml.csh``. 
`CAM_CONFIG_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `CAM_NAMELIST_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `CAM_NML_USECASE <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are used to set compset variables (e.g., "-phys cam5" for CAM_CONFIG_OPTS) and in general should not be modified for supported compsets. 
For a complete documentation of namelist settings, see `CAM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
To modify CAM namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_cam`` file (see the documentation for each file at the top of that file). 
For example, to change the solar constant to 1363.27, modify the ``user_nl_cam`` file to contain the following line at the end "solar_const=1363.27". 
To see the result of adding this, call **preview_namelists** and verify that this new value appears in ``CaseDocs/atm_in``.

CLM
^^^
CLM's `configure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `build-namelist <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ utilities are called by ``Buildconf/clm.buildnml.csh``. `CLM_CONFIG_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `CLM_NML_USE_CASE <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are used to set compset specific variables and in general should not be modified for supported compsets. For a complete documentation of namelist settings, see `CLM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. To modify CLM namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_clm`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/lnd_in``.

RTM
^^^
RTM's **build-namelist** utility is called by ``Buildconf/rtm.buildnml.csh``. For a complete documentation of namelist settings, see RTM namelist variables. To modify `RTM namelist settings <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_rtm`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/rof_in``.

CICE
^^^^
CICE's `configure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `build-namelist <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ utilities are now called by ``Buildconf/cice.buildnml.csh``. Note that `CICE_CONFIG_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, and `CICE_NAMELIST_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are used to set compset specific variables and in general should not be modified for supported compsets. For a complete documentation of namelist settings, see `CICE namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. To modify CICE namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_cice`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/ice_in``.

In addition, **cesm_setup** creates CICE's compile time `block decomposition variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ in ``env_build.xml`` as follows:
::

   ./case.setup
     ⇓
   Buildconf/cice.buildnml.csh and $NTASKS_ICE and $NTHRDS_ICE
     ⇓
   env_build.xml variables CICE_BLCKX, CICE_BLCKY, CICE_MXBLCKS, CICE_DECOMPTYPE 
   CPP variables in cice.buildexe.csh
   

POP2
^^^^
See `POP2 namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a complete description of the POP2 run-time namelist variables. Note that `OCN_COUPLING, OCN_ICE_FORCING, OCN_TRANSIENT <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are normally utilized ONLY to set compset specific variables and should not be edited. For a complete documentation of namelist settings, see `CICE namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. To modify POP2 namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_pop2`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/ocn_in``.

In addition, **cesm_setup** also generates POP2's compile time compile time `block decomposition variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ in ``env_build.xml`` as follows:
::

   ./cesm_setup  
       ⇓
   Buildconf/pop2.buildnml.csh and $NTASKS_OCN and $NTHRDS_OCN
       ⇓
   env_build.xml variables POP2_BLCKX, POP2_BLCKY, POP2_MXBLCKS, POP2_DECOMPTYPE 
   CPP variables in pop2.buildexe.csh

CISM
^^^^
See `CISM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a complete description of the CISM run-time namelist variables. This includes variables that appear both in ``cism_in`` and in ``cism.config``. To modify any of these settings, you should add the appropriate keyword/value pair at the end of the ``user_nl_cism`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/cism_in`` and ``CaseDocs/cism.config``.

There are also some run-time settings set via ``env_run.xml``, as documented in `CISM run time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ - in particular, the model resolution, set via ``CISM_GRID``. The value of ``CISM_GRID`` determines the default value of a number of other namelist parameters.


Customizing ACME prognostic component-specific namelist settings
----------------------------------------------------------------

Controlling output data
-----------------------

During a model run, each CESM component produces its own output datasets consisting of history, restart and output log files. Component history files and restart files are in netCDF format. Restart files are used to either exactly restart the model or to serve as initial conditions for other model cases.

Archiving is a phase of a CESM model run where the generated output data is moved from $RUNDIR to a local disk area (short-term archiving) and subsequently to a long-term storage system (long-term archiving). It has no impact on the production run except to clean up disk space and help manage user quotas. Although short-term and long-term archiving are implemented independently in the scripts, there is a dependence between the two since the short-term archiver must be turned on in order for the long-term archiver to be activated. In ``env_run.xml``, several variables control the behavior of short and long-term archiving. See `short and long term archiving <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a description of output data control variables. Several important points need to be made about both short and long term archiving:

- By default, short-term archiving is enabled and long-term archiving is disabled.

- All output data is initially written to ``$RUNDIR``.

- Unless a user explicitly turns off short-term archiving, files will be moved to ``$DOUT_S_ROOT`` at the end of a successful model run.

- If long-term archiving is enabled, files will be moved to ``$DOUT_L_MSROOT`` by ``$CASE.l_archive``, which is run as a separate batch job after the successful completion of a model run.

- Users should generally turn off short term-archiving when developing new CESM code.

- If long-term archiving is not enabled, users must monitor quotas and usage in the ``$DOUT_S_ROOT/`` directory and should manually clean up these areas on a frequent basis.

Standard output generated from each CESM component is saved in a "log file" for each component in $RUNDIR. Each time the model is run, a single coordinated datestamp is incorporated in the filenames of all output log files associated with that run. This common datestamp is generated by the run script and is of the form YYMMDD-hhmmss, where YYMMDD are the Year, Month, Day and hhmmss are the hour, minute and second that the run began (e.g. ocn.log.040526-082714). Log files are also copied to a user specified directory using the variable $LOGDIR in ``env_run.xml``. The default is a 'logs' subdirectory beneath the case directory.

By default, each component also periodically writes history files (usually monthly) in netCDF format and also writes netCDF or binary restart files in the $RUNDIR directory. The history and log files are controlled independently by each component. History output control (i.e. output fields and frequency) is set in the ``Buildconf/$component.buildnml.csh`` files.

The raw history data does not lend itself well to easy time-series analysis. For example, CAM writes one or more large netCDF history file(s) at each requested output period. While this behavior is optimal for model execution, it makes it difficult to analyze time series of individual variables without having to access the entire data volume. Thus, the raw data from major model integrations is usually postprocessed into more user-friendly configurations, such as single files containing long time-series of each output fields, and made available to the community.

As an example, for the following example settings:
```
DOUT_S = TRUE
DOUT_S_ROOT = /ptmp/$user/archive
DOUT_L_MS = TRUE
DOUT_L_MSROOT /USER/csm/$CASE
```
the run will automatically submit the **$CASE.l_archive** to the queue upon its completion to archive the data. The system is not bulletproof, and you will want to verify at regular intervals that the archived data is complete, particularly during long running jobs.


Load Balancing a Case
---------------------

Load balancing refers to the optimization of the processor layout for a given model configuration (compset, grid, etc) such that the cost and throughput will be optimal. 
Optimal is a somewhat subjective thing. 
For a fixed total number of processors, it means achieving the maximum throughput. 
For a given configuration across varied processor counts, it means finding several "sweet spots" where the model is minimally idle, the cost is relatively low, and the throughput is relatively high. 
As with most models, increasing total processors normally results in both increased throughput and increased cost. 
If models scaled linearly, the cost would remain constant across different processor counts, but generally, models don't scale linearly and cost increases with increasing processor count. 
This is certainly true for CESM. It is strongly recommended that a user perform a load-balancing exercise on their proposed model run before undertaking a long production run.

CESM has significant flexibility with respect to the layout of components across different hardware processors. 
In general, there are seven unique models (atm, lnd, rof, ocn, ice, glc, cpl) that are managed independently in CESM, each with a unique MPI communicator. In addition, the driver runs on the union of all processors and controls the sequencing and hardware partitioning.

Please see the section on `setting the case PE layout <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a detailed discussion of how to set processor layouts and the example on `changing the PE layout <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

Model timing data
^^^^^^^^^^^^^^^^^

In order to perform a load balancing exercise, you must first be aware of the different types of timing information produced by every CESM run. How this information is used is described in detail in `using model timing data <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

A summary timing output file is produced after every CESM run. This file is placed in ``$CASEROOT/timing/ccsm_timing.$CASE.$date``, where $date is a datestamp set by CESM at runtime, and contains a summary of various information. The following provides a description of the most important parts of a timing file.

The first section in the timing output, CCSM TIMING PROFILE, summarizes general timing information for the run. The total run time and cost is given in several metrics including pe-hrs per simulated year (cost), simulated years per wall day (thoughput), seconds, and seconds per model day. This provides general summary information quickly in several units for analysis and comparison with other runs. The total run time for each component is also provided, as is the time for initialization of the model. These times are the aggregate over the total run and do not take into account any temporal or processor load imbalances.

The second section in the timing output, "DRIVER TIMING FLOWCHART", provides timing information for the driver in sequential order and indicates which processors are involved in the cost. Finally, the timings for the coupler are broken out at the bottom of the timing output file.

Separately, there is another file in the timing directory, ccsm_timing_stats.$date that accompanies the above timing summary. This second file provides a summary of the minimum and maximum of all the model timers.

There is one other stream of useful timing information in the cpl.log.$date file that is produced for every run. The cpl.log file contains the run time for each model day during the model run. This diagnostic is output as the model runs. You can search for tStamp in the cpl.log file to see this information. This timing information is useful for tracking down temporal variability in model cost either due to inherent model variability cost (I/O, spin-up, seasonal, etc) or possibly due to variability due to hardware. The model daily cost is generally pretty constant unless I/O is written intermittently such as at the end of the month.

Using model timing data
^^^^^^^^^^^^^^^^^^^^^^^

In practice, load-balancing requires a number of considerations such as which components are run, their absolute and relative resolution; cost, scaling and processor count sweet-spots for each component; and internal load imbalance within a component. It is often best to load balance the system with all significant run-time I/O turned off because this occurs very infrequently, typically one timestep per month, and is best treated as a separate cost as it can bias interpretation of the overall model load balance. Also, the use of OpenMP threading in some or all of the components is dependent on the hardware/OS support as well as whether the system supports running all MPI and mixed MPI/OpenMP on overlapping processors for different components. A final point is deciding whether components should run sequentially, concurrently, or some combination of the two with each other. Typically, a series of short test runs is done with the desired production configuration to establish a reasonable load balance setup for the production job. The timing output can be used to compare test runs to help determine the optimal load balance.

Changing the pe layout of the model has NO IMPACT on the scientific results. The basic order of operations and calling sequence is hardwired into the driver and that doesn't change when the pe layout is changed. There are some constraints on the ability of CESM to run fully concurrent. In particular, the atmosphere model always run sequentially with the ice and land for scientific reasons. As a result, running the atmosphere concurrently with the ice and land will result in idle processors in these components at some point in the timestepping sequence. For more information about how the driver is implemented, see (Craig, A.P., Vertenstein, M., Jacob, R., 2012: A new flexible coupler for earth system modeling developed for CCSM4 and CESM1.0. International Journal of High Performance Computing Applications, 26, 31-42, 10.1177/1094342011428141). As of CESM1.1.1, there is a new separate rof component. That component is implemented in the driver just like the land model. It can run concurrently with the land model but not concurrently with the atmosphere model.

In general, we normally carry out 20-day model runs with restarts and history turned off in order to find the layout that has the best load balance for the targeted number of processors. This provides a reasonable performance estimate for the production run for most of the runtime. The end of month history and end of run restart I/O is treated as a separate cost from the load balance perspective. To set up this test configuration, create your production case, and then edit env_run.xml and set STOP_OPTION to ndays, STOP_N to 20, and RESTART_OPTION to never. Seasonal variation and spin-up costs can change performance over time, so even after a production run has started, it's worthwhile to occasionally review the timing output to see whether any changes might be made to the layout to improve throughput or decrease cost.

In determining an optimal load balance for a specific configuration, two pieces of information are useful.

- Determine which component or components are most expensive.

- Understand the scaling of the individual components, whether they run faster with all MPI or mixed MPI/OpenMP decomposition strategies, and their optimal decompositions at each processor count. If the cost and scaling of the components are unknown, several short tests can be carried out with arbitrary component pe counts just to establish component scaling and sweet spots.

One method for determining an optimal load balance is as follows

- start with the most expensive component and a fixed optimal processor count and decomposition for that component

- test the systems, varying the sequencing/concurrency of the components and the pe counts of the other components

- identify a few best potential load balance configurations and then run each a few times to establish run-to-run variability and to try to statistically establish the faster layout

In all cases, the component run times in the timing output file can be reviewed for both overall throughput and independent component timings. Using the timing output, idle processors can be identified by considering the component concurrency in conjunction with the component timing.

In general, there are only a few reasonable component layout options for CESM.

- fully sequential

- fully sequential except the ocean running concurrently

- fully concurrent except the atmosphere run sequentially with the ice, rof, and land components

- finally, it makes best sense for the coupler to run on a subset of the atmosphere processors and that can be sequentially or concurrently run with the land and ice

The concurrency is limited in part by the hardwired sequencing in the driver. This sequencing is set by scientific constraints, although there may be some addition flexibility with respect to concurrency when running with mixed active and data models.

There are some general rules for finding optimal configurations:

- Make sure you have set a processor layout where each hardware processor is assigned to at least one component. There is rarely a reason to have completely idle processors in your layout.

- Make sure your cheapest components keep up with your most expensive components. In other words, a component that runs on 1024 processors should not be waiting on a component running on 16 processors.

- Before running the job, make sure the batch queue settings in the $CASE.run script are set correctly for the specific run being targetted. The account numbers, queue names, time limits should be reviewed. The ideal time limit, queues, and run length are all dependent on each other and on the current model throughput.

- Make sure you are taking full advantage of the hardware resources. If you are charged by the 32-way node, you might as well target a total processor count that is a multiple of 32.

- If possible, keep a single component on a single node. That usually minimizes internal component communication cost. That's obviously not possible if running on more processors than the size of a node.

- And always assume the hardware performance could have variations due to contention on the interconnect, file systems, or other areas. If unsure of a timing result, run cases multiple times.


How do I run a case?
-----------------------

Setting the time limits
^^^^^^^^^^^^^^^^^^^^^^^

Before you can run the job, you need to make sure the batch queue variables are set correctly for the specific run being targeted. This is done currently by manually editing ``$CASE.run``. You should carefully check the batch queue submission lines and make sure that you have appropriate account numbers, time limits, and stdout file names. In looking at the ccsm_timing.$CASE.$datestamp files for "Model Throughput", output like the following will be found:

```
Overall Metrics:
Model Cost: 327.14 pe-hrs/simulated_year (scale= 0.50)
Model Throughput: 4.70 simulated_years/day
```

The model throughput is the estimated number of model years that you can run in a wallclock day. Based on this, you can maximize $CASE.run queue limit and change $STOP_OPTION and $STOP_N in ``env_run.xml``. For example, say a model's throughput is 4.7 simulated_years/day. On yellowstone(??), the maximum runtime limit is 6 hours. 4.7 model years/24 hours * 6 hours = 1.17 years. On the massively parallel computers, there is always some variability in how long it will take a job to run. On some machines, you may need to leave as much as 20% buffer time in your run to guarantee that jobs finish reliably before the time limit. For that reason we will set our model to run only one model year/job. Continuing to assume that the run is on yellowstone, in ``$CASE.yellowstone.run set``:

```
#BSUB -W 6:00
```

and ``xmlchange`` should be invoked as follows in ``CASEROOT``:

```
./xmlchange STOP_OPTION=nyears
./xmlchange STOP_N=1 
./xmlchange REST_OPTION=nyears
./xmlchange REST_N=1 
```

Submitting the run
^^^^^^^^^^^^^^^^^^^^^^^

Once you have configured and built the model, submit $CASE.run to your machine's batch queue system using the ``$CASE.submit`` command.

```
> $CASE.submit 
```

You can see a complete example of how to run a case in `the basic example <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

When executed, the run script, ``$CASE.run``:

- Will not execute the build script. Building CESM is now done only via an interactive call to the build script, ``$CASE.build``.

- Will check that locked files are consistent with the current xml files, run the buildnml script for each component and verify that required input data is present on local disk (in ``$DIN_LOC_ROOT``).

- Will run the CESM model.

- Upon completion, will put timing information in ``$LOGDIR/timing`` and copy log files back to ``$LOGDIR``

- If ``$DOUT_S`` is TRUE, component history, log, diagnostic, and restart files will be moved from ``$RUNDIR`` to the short-term archive directory, ``$DOUT_S_ROOT``.

- If ``$DOUT_L_MS`` is TRUE, the long-term archiver, ``$CASE.l_archive``, will be submitted to the batch queue upon successful completion of the run.

- If ``$RESUBMIT`` >0, resubmit ``$CASE.run``

If the job runs to completion, you should have "SUCCESSFUL TERMINATION OF CPL7-CCSM" near the end of your STDOUT file. New data should be in the subdirectories under $DOUT_S_ROOT, or if you have long-term archiving turned on, it should be automatically moved to subdirectories under $DOUT_L_MSROOT.

If the job failed, there are several places where you should look for information. Start with the STDOUT and STDERR file(s) in $CASEROOT. If you don't find an obvious error message there, the $RUNDIR/$model.log.$datestamp files will probably give you a hint. First check cpl.log.$datestamp, because it will often tell you when the model failed. Then check the rest of the component log files. Please see `troubleshooting runtime errors <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for more information.

REMINDER: Once you have a successful first run, you must set CONTINUE_RUN to TRUE in ``env_run.xml`` before resubmitting, otherwise the job will not progress. You may also need to modify the `STOP_OPTION, STOP_N and/or STOP_DATE <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `REST_OPTION, REST_N and/or REST_DATE <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, and `RESUBMIT <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ variables in ``env_run.xml`` before resubmitting.

Restarting a run
^^^^^^^^^^^^^^^^^^^^^^^

Restart files are written by each active component (and some data components) at intervals dictated by the driver via the setting of the ``env_run.xml`` variables, ``$REST_OPTION`` and ``$REST_N``. Restart files allow the model to stop and then start again with bit-for-bit exact capability (i.e. the model output is exactly the same as if it had never been stopped). The driver coordinates the writing of restart files as well as the time evolution of the model. All components receive restart and stop information from the driver and write restarts or stop as specified by the driver.

It is important to note that runs that are initialized as branch or hybrid runs, will require restart/initial files from previous model runs (as specified by the variables, ``$RUN_REFCASE`` and ``$RUN_REFDATE``). These required files must be prestaged by the user to the case ``$RUNDIR`` (normally ``$EXEROOT/run``) before the model run starts. This is normally done by just copying the contents of the relevant ``$RUN_REFCASE/rest/$RUN_REFDATE.00000`` directory.

Whenever a component writes a restart file, it also writes a restart pointer file of the form, ``rpointer.$component``. The restart pointer file contains the restart filename that was just written by the component. Upon a restart, each component reads its restart pointer file to determine the filename(s) to read in order to continue the model run. As examples, the following pointer files will be created for a component set using full active model components.

```
- rpointer.atm
- rpointer.drv
- rpointer.ice
- rpointer.lnd
- rpointer.rof
- rpointer.cism
- rpointer.ocn.ovf
- rpointer.ocn.restart
```

If short-term archiving is turned on, then the model archives the component restart datasets and pointer files into ``$DOUT_S_ROOT/rest/yyyy-mm-dd-sssss``, where yyyy-mm-dd-sssss is the model date at the time of the restart (see `below for more details <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). If long-term archiving these restart then archived in ``$DOUT_L_MSROOT/rest``. ``DOUT_S_ROOT`` and ``DOUT_L_MSROOT`` are set in ``env_run.xml``, and can be changed at any time during the run.

Backing up to a previous restart
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a run encounters problems and crashes, you will normally have to back up to a previous restart. Assuming that short-term archiving is enabled, you will need to find the latest ``$DOUT_S_ROOT/rest/yyyy-mm-dd-ssss/`` directory that was created and copy the contents of that directory into your run directory (``$RUNDIR``). You can then continue the run and these restarts will be used. It is important to make sure the new rpointer.* files overwrite the rpointer.* files that were in ``$RUNDIR``, or the job may not restart in the correct place.

Occasionally, when a run has problems restarting, it is because the rpointer files are out of sync with the restart files. The rpointer files are text files and can easily be edited to match the correct dates of the restart and history files. All the restart files should have the same date.

Data flow during a model run
----------------------------

All component log files are copied to the directory specified by the ``env_run.xml`` variable ``$LOGDIR`` which by default is set to ``$CASEROOT/logs``. This location is where log files are copied when the job completes successfully. If the job aborts, the log files will NOT be copied out of the ``$RUNDIR`` directory.

Once a model run has completed successfully, the output data flow will depend on whether or not short-term archiving is enabled (as set by the ``env_run.xml`` variable, ``$DOUT_S``). By default, short-term archiving will be done.

No archiving
^^^^^^^^^^^^

If no short-term archiving is performed, then all model output data will remain in the run directory, as specified by the ``env_run.xml`` variable, ``$RUNDIR``. Furthermore, if short-term archiving is disabled, then long-term archiving will not be allowed.

Short-term archiving
^^^^^^^^^^^^^^^^^^^^

If short-term archiving is enabled, the component output files will be moved to the short term archiving area on local disk, as specified by ``$DOUT_S_ROOT``. The directory ``DOUT_S_ROOT`` is normally set to ``$EXEROOT/../archive/$CASE.`` and will contain the following directory structure:
::

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

logs/ contains component log files created during the run. In addition to ``$LOGDIR``, log files are also copied to the short-term archiving directory and therefore are available for long-term archiving.

rest/ contains a subset of directories that each contain a *consistent* set of restart files, initial files and rpointer files. Each sub-directory has a unique name corresponding to the model year, month, day and seconds into the day where the files were created (e.g. 1852-01-01-00000/). The contents of any restart directory can be used to `create a branch run or a hybrid run <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ or back up to a previous restart date.

Long-term archiving
^^^^^^^^^^^^^^^^^^^

For long production runs that generate many giga-bytes of data, you will normally want to move the output data from local disk to a long-term archival location. Long-term archiving can be activated by setting ``$DOUT_L_MS`` to TRUE in ``env_run.xml``. By default, the value of this variable is FALSE, and long-term archiving is disabled. If the value is set to TRUE, then the following additional variables are: ``$DOUT_L_MSROOT, $DOUT_S_ROOT DOUT_S`` (see 
`variables for output data management <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_).

As was mentioned above, if long-term archiving is enabled, files will be moved out of ``$DOUT_S_ROOT`` to ``$DOUT_L_ROOT`` by ``$CASE.l_archive``, which is run as a separate batch job after the successful completion of a model run.

