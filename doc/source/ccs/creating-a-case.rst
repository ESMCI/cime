.. _ccs_create_newcase:

Creating a Case
===============

.. contents::
   :local:

After determining a ``compset`` and ``grid`` a case can be created.

User Mods
---------
A case can customized by providing **user mods** when creating a new case. The **user mods** provide a few ways to customize a case. 

* Namelist files
* Source code modifications
* Shell commands (can call ``xmlchange``)

This can be useful when a user wants to carry out a series of experiments based on a common set of changes to the namelists, source code, and/or case XML settings.

Here's an example **user mod** to demonstrate.

::

    mkdir ./usermod
    echo "nlmaps_verbosity = 1" >> ./usermod/user_nl_cpl
    echo "./xmlchange NTASKS=80" >> ./usermod/shell_commands
    ./scripts/create_newcase --compset S --res f19_g16 --case ./case01 --user-mods-dir ./usermod

.. important::

    It is important to note that the file containing the **xmlchange** 
    commands must be named ``shell_commands`` in order for it to be recognized
    and run upon case creation.

The structure of the component directories does not need to be the 
same as in the component source code. As an example, should the user
want to modify the ``src/dynamics/eul/dyncomp.F90`` file within the 
CAM source code, the modified file should be put into the directory 
``SourceMods/src.cam`` directly. There is no need to mimic the source
code structure, such as ``SourceMods/src.cam/dynamics/eul``.

Creating a new Case
-------------------
The first step in creating a CIME case is to call ``create_newcase``.
This script is used to create a new case directory and populate it with the necessary files to build and run the model.

The following command demonstrates the three required options for creating a new case: the case name, compset, and model grid.

::

    ./scripts/create_newcase --case <name> --compset <compset> --res <model grid>

.. warning::

    The ``--case`` argument must be a string and may not contain any of the following special characters

    ::

        > + * ? < > { } [ ] ~ ` @ :

The ``<name>`` value can be a simple name or an relative/absolute path. If it's a simple name then the case will be created in the current directory. If it's a relative/absolute path then the case will be created in there.

User Scripts
````````````
===================== ===========
Script                Description
===================== ===========
case.build            Script to build component and utility libraries and model executable.
case.cmpgen_namelists Script to perform namelist baseline operations (compare, generate, or both).
case.qstatus          Script to query the queue on any queue system.
case.setup            Script used to set up the case (create the case.run script, Macros file, and user_nl_xxx files).
case.submit           Script to submit the case to run using the machine's batch queuing system.
check_case            Script to verify the case is set up correctly.
check_input_data      Script for checking for various input data sets and moving them into place.
pelayout              Script to query and modify the NTASKS, ROOTPE, and NTHRDS for each component model.
preview_namelists     Script for users to see their component namelists in ``$CASEROOT/CaseDocs`` before running the model.
preview_run           Script for users to see batch submit and mpirun commands.
xmlchange             Script to modify values in the XML files.
xmlquery              Script to query values in the XML files.
===================== ===========

XML Files
`````````
======================= ============================
File                    Description
======================= ============================
env_archive.xml         Defines patterns of files to be sent to the short-term archive. You can edit this file at any time. You **CANNOT** use ``xmlchange`` to modify variables in this file.
env_batch.xml           Sets batch system settings such as wallclock time and queue name.
env_build.xml           Sets model build settings. This includes component resolutions and component compile-time configuration options. You must run the case.build command after changing this file.
env_case.xml            Parameters set by create_newcase.
env_mach_pes.xml        Sets component machine-specific processor layout (see changing pe layout). The settings in this are critical to a well-load-balanced simulation (see :ref:`load balancing <optimizing-processor-layout>`).
env_mach_specific.xml   Sets a number of machine-specific environment variables for building and/or running. You **CANNOT** use ``xmlchange`` to modify variables in this file.
env_run.xml             Sets runtime settings such as length of run, frequency of restarts, output of coupler diagnostics, and short-term and long-term archiving. This file can be edited at any time before a job starts.
env_workflow.xml        Sets parameters for the runtime workflow.
======================= ============================

Source Mods Directory
``````````````````````````
=========== ===============
Directory   Description
=========== ===============
SourceMods  Top-level directory containing subdirectories for each compset component where you can place modified source code for that component. You may also place modified buildnml and buildlib scripts here.
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
LockedFiles     Work directory that holds copies of files that should not be changed. Certain XML files are *locked* after their variables have been used and should no longer be changed (see below).
Tools           Work directory containing support utility scripts. You should never need to edit the contents of this directory.
=============== ===========================

Locked files
````````````
The ``$CASEROOT`` XML files are organized so that variables can be
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
