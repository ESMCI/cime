Creating a Case
===============

.. contents::
   :local:

This section will provide details on creating a case using CCS. In order to follow along you will need to ensure the machine
you're on is currently supported by your model.

You can use `query_config` to check if your machine is supported.

::

    ./scripts/query_config --machines

If you do not find your current machine in the output you will need to :ref:`port <porting>` CIME to your machine.

Calling **create_newcase**
--------------------------

The first step in creating a CIME-based experiment is to use ``create_newcase``.

Review the **help** text for all the available options.

::

    ./scripts/create_newcase --help

There are only three required arguments for the ``create_newcase`` command.

::

    ./scripts/create_newcase --case CASENAME --compset COMPSET --res GRID

Creating a CIME experiment or *case* requires, at a minimum, specifying a compset (COMPSET) and a model grid (GRID) and a case directory (CASENAME).

.. warning::

    The ``--case`` argument must be a string and may not contain any of the following special characters

    ::

        > + * ? < > { } [ ] ~ ` @ :

The ``--case`` argument is used to define the name of your case, a very important piece of
metadata that will be used in filenames, internal metadata and directory paths. The
``CASEROOT`` is a directory create_newcase will create with the same name as the
``CASENAME``. If ``CASENAME`` is simply a name (not a path), ``CASEROOT`` is created in
the directory where you execute create_newcase. If ``CASENAME`` is a relative or absolute
path, ``CASEROOT`` is created there, and the name of the case will be the last component
of the path.

Output from **create_newcase**
------------------------------

Suppose **create_newcase** was called as follows.

This command should be ran from ``$CIMEROOT`` which is the root directory of your CIME repository.

::

    ./scripts/create_newcase --case ~/cime/example1 --compset S --res f19_g16

In the example, the command creates a ``$CASEROOT`` directory: ``~/cime/example1``.
If that directory already exists, a warning is printed and the command aborts.

In the argument to ``--case``, the case name is taken from the string after the last slash
--- so here the case name is ``example1``.

The output from the command may look like the following, which includes lots of useful information.

::

    Compset longname is 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_SWAV_SESP
    Compset specification file is /src/work/E3SM/driver-mct/cime_config/config_compsets.xml
    Automatically adding SIAC to compset
    Compset forcing is 
    Com forcing is present day:
    ATM component is Stub atm component
    LND component is Stub land component
    ICE component is Stub ice component
    OCN component is Stub ocn component
    ROF component is Stub river component
    GLC component is Stub glacier (land ice) component
    WAV component is Stub wave component
    IAC component is Stub iac component
    ESP component is Stub external system processing (ESP) component
    Pes     specification file is /src/work/E3SM/driver-mct/cime_config/config_pes.xml
    WARNING: User-selected machine 'docker' does not match probed machine 'ghci-snl-cpu'
    Pes setting: compset_match is SATM 
    Pes setting: grid          is a%null_l%null_oi%null_r%null_g%null_w%null_z%null_m%gx1v6 
    Pes setting: compset       is 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_SWAV_SIAC_SESP 
    Pes setting: tasks       is {'NTASKS_ATM': 8, 'NTASKS_LND': 8, 'NTASKS_ROF': 8, 'NTASKS_ICE': 8, 'NTASKS_OCN': 8, 'NTASKS_GLC': 8, 'NTASKS_WAV': 8, 'NTASKS_CPL': 8} 
    Pes setting: threads     is {} 
    Pes setting: rootpe      is {} 
    Pes setting: pstrid      is {} 
    Pes other settings: {}
    Pes other settings append: {}
    Pes comments: driver-mct: any grid, any mach, compset SATM, any pesize
    setting additional fields from config_pes: {}, append {}
     Compset is: 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_SWAV_SIAC_SESP 
     Grid is: a%null_l%null_oi%null_r%null_g%null_w%null_z%null_m%gx1v6 
     Components in compset are: ['satm', 'slnd', 'sice', 'socn', 'srof', 'sglc', 'swav', 'siac', 'sesp'] 
    Using project from config_machines.xml: CIME
    No charge_account info available, using value from PROJECT
    e3sm model version found: fa90280312
    Batch_system_type is none
     Creating Case directory /root/cime/example1

The ``create_newcase`` command installs files in ``$CASEROOT`` that will build and run the model. Scripts to optionally archive the case on the target platform are provided as well.

Running ``create_newcase`` provides the following scripts, files, and directories in ``$CASEROOT``:

User Scripts
````````````
===================== ===========
Script                Description
===================== ===========
case.build            Script to build component and utility libraries and model executable.
case.cmpgen_namelists Script to perform namelist baseline operations (compare, generate, or both)."
case.qstatus          Script to query the queue on any queue system.
case.setup            Script used to set up the case (create the case.run script, Macros file and user_nl_xxx files).
case.submit           Script to submit the case to run using the machine's batch queueing system.
check_case            Script to verify case is set up correctly.
check_input_data      Script for checking for various input data sets and moving them into place.
pelayout              Script to query and modify the NTASKS, ROOTPE, and NTHRDS for each component model.
preview_namelists     Script for users to see their component namelists in ``$CASEROOT/CaseDocs`` before running the model.
preview_run           Script for users to see batch submit and mpirun command."
xmlchange             Script to modify values in the xml files.
xmlquery              Script to query values in the xml files.
===================== ===========

XML Files
`````````
======================= ============================
File                    Description
======================= ============================
env_archive.xml         Defines patterns of files to be sent to the short-term archive. You can edit this file at any time. You **CANNOT** use ``xmlchange`` to modify variables in this file.
env_batch.xml           Sets batch system settings such as wallclock time and queue name.
env_build.xml           Sets model build settings. This includes component resolutions and component compile-time configuration options. You must run the case.build command after changing this file.
env_case.xml            Parameters set by create_newcase
env_mach_pes.xml        Sets component machine-specific processor layout (see changing pe layout ). The settings in this are critical to a well-load-balanced simulation (see :ref:`load balancing <optimizing-processor-layout>`).
env_mach_specific.xml   Sets a number of machine-specific environment variables for building and/or running. You **CANNOT** use ``xmlchange`` to modify variables in this file.
env_run.xml             Sets runtime settings such as length of run, frequency of restarts, output of coupler diagnostics, and short-term and long-term archiving. This file can be edited at any time before a job starts.
env_workflow.xml        Sets paramateres for the runtime workflow.
======================= ============================

User Source Mods Directory
``````````````````````````
=========== ===============
Directory   Description
=========== ===============
SourceMods  Top-level directory containing subdirectories for each compset component where you can place modified source code for that component. You may also place modified buildnml and buildlib scripts here."
=========== ===============

Provenance
``````````
=============== =======================
File            Description
=============== =======================
README.case     File detailing ``create_newcase`` usage. This is a good place to keep track of runtime problems and changes.
replay.sh       This file is a record of all commands used, and can be used to recreate a case.
=============== =======================

Non-modifiable work directories
```````````````````````````````
=============== ===========================
Directory       Description
=============== ===========================
Buildconf       Work directory containing scripts to generate component namelists and component and utility libraries (PIO or MCT, for example). You should never have to edit the contents of this directory.
LockedFiles     Work directory that holds copies of files that should not be changed. Certain xml files are *locked* after their variables have been used by should no longer be changed (see below).
Tools           Work directory containing support utility scripts. You should never need to edit the contents of this directory."
=============== ===========================

Locked files in your case directory
-----------------------------------

The ``$CASEROOT`` xml files are organized so that variables can be
locked at certain points after they have been resolved (used) in other
parts of the scripts system.

CIME does this by *locking* a file in ``$CASEROOT/LockedFiles`` and
not permitting you to modify that file unless, depending on the file,
you call ``case.setup --clean`` or ``case.build --clean``.

CIME locks your ``$CASEROOT`` files according to the following rules:

* ``create_newcase`` will lock **env_case.xml** which can never be unlocked.
* ``case.setup`` will lock **env_mach_pes.xml**, this can be unlocked with ``case.setup --clean``.
* ``case.build`` will lock **env_build.xml**, this can be unlocked with ``case.build --clean``.
* The **env_run.xml**, **env_batch.xml**, and **env_archive.xml** files are never locked, and most can be changed at any time.

.. note::

    There are some exceptions in the **env_batch.xml** file.

User Mods
---------

A user can customize a case by providing a **user mods** when creating a new case. The **user mods** provides a few ways to customize a case. 

* Namelist files
* Source code modifications
* Shell commands (can call ``xmlchange``)

This can be useful when a user wants to carry out a series of experiments based on a common set of changes to the namelists, source code and/or case xml settings.

Here's a toy **user mod** to demonstrate.

::

    mkdir ./usermod
    echo "nlmaps_verbosity = 1" >> ./usermod/user_nl_cpl
    echo "./xmlchange NTASKS=80" >> ./usermod/shell_commands
    ./scripts/create_newcase --compset S --res f19_g16 --case ./case01 --user-mods-dir ./usermod

.. important::

    It is important to note that the file containing the **xmlchange** 
    commands must be named ``shell_commands`` in order for it to be recognised
    and run upon case creation.

The structure of the component directories do not need to be the 
same as in the component source code. As an example, should the user
want to modify the ``src/dynamics/eul/dyncomp.F90`` file within the 
CAM source code, the modified file should be put into the directory 
``SourceMods/src.cam`` directly. There is no need to mimic the source
code structure, such as ``SourceMods/src.cam/dynamics/eul``.
