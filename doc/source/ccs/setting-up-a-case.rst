.. _ccs_setting_up_a_case:

Setting up a Case
=================

.. contents::
    :local:

Configuration
-------------
After creating a case, some aspects of the configuration are fixed (any variables in ``env_case.xml``). But many can be changed before calling ``case.setup``, which generates the files required to build and run the case. CIME provides ``xmlquery`` to view and ``xmlchange`` to modify the variables used in this process.

.. _ccs_xmlquery:
Querying
`````````
CIME provides the ``xmlquery`` command to view the configuration of a case. The configuration is a collection of variables stored in XML files. These variables are grouped together when defined in the model's configuration.

The following will list all of the current configuration.

.. code-block:: bash

    ./xmlquery --listall

To view a specific group, replace ``<group>`` with the desired group name.

.. code-block:: bash

    ./xmlquery --subgroup <group> --listall

.. _ccs_xmlchange:
Modifying
`````````
The ``xmlchange`` command is used to modify the configuration of a case. The following will change the value of a variable.

.. code-block:: bash
    
    ./xmlchange <variable>=<value>

Some variables can exist in multiple groups. To change a variable in a specific group, use the ``--subgroup`` option.

.. code-block:: bash

    ./xmlchange JOB_WALLCLOCK_TIME=0:30 --subgroup case.run

Setting up the Case
-------------------
Once all the configuration is done, it's time to call ``case.setup`` from ``$CASEROOT``. This will generate the files required to build and run the case.

.. warning::
    
    If ``xmlchange`` is called after ``case.setup``, the changes will not be reflected in the generated files. To update the files, call ``case.setup --reset``.

Tracking changes with Git
`````````````````````````
When you set up a case, a new Git repository will be created within the ``$CASEROOT`` directory if a recent version of Git is installed. The repository will have a branch named after the case.

.. warning::
    
    If you are using a version of Git older than 2.28, the repository will not be created automatically. In this case, you can create a repository manually and push the case to it.

Each time you run ``case.setup``, ``case.build``, ``case.submit``, or ``xmlchange``, a new commit is created. This allows you to track changes to the case over time.

If you set the ``CASE_GIT_REPOSITORY`` variable to a valid Git repository URL, the case will be pushed to that repository where the branch name is the case name.

.. code-block:: bash

    ./xmlchange CASE_GIT_REPOSITORY=<repository>

.. note::

    To disable this feature, call ``case.setup --disable-git``.

Generated files
```````````````
The following files and directories are generated in ``$CASEROOT``:

=============================   ===============================================================================================================================
.case.run                       A (hidden) file with the commands that will be used to run the model (such as “mpirun”) and any batch directives needed. The directive values are generated using the contents of **env_mach_pes.xml**. Running ``case.setup`` will remove this file. This file should not be edited directly and instead controlled through XML variables in **env_batch.xml**. It should also *never* be run directly.
.env_mach_specific.*            Files summarizing the **module load** commands and environment variables that are set when the scripts in ``$CASEROOT`` are called. These files are not used by the case but can be useful for debugging **module load** and environment settings.
CaseDocs/                       Directory that contains all the component namelists for the run. This is for reference only and files in this directory SHOULD NOT BE EDITED since they will be overwritten at build time and runtime.
CaseStatus                      File containing a list of operations done in the current case.
Depends.*                       Lists of source code files that need special build options.
Macros.cmake                    File containing machine-specific makefile directives for your target platform/compiler. This file is created if it does not already exist. The user can modify the file to change certain aspects of the build, such as compiler flags. Running ``case.setup --clean`` will not remove the file once it has been created. However, if you remove or rename the Macros.make file, running ``case.setup`` recreates it.
case.st_archive                 Script to perform short-term archiving to disk for your case output. Note that this script is run automatically by the normal CIME workflow.
cmake_macros/                   Directory containing any CMake macros required for the machine/compiler combination.
user_nl_xxx[_NNNN]              Files where all user modifications to component namelists are made. **xxx** is any one of the set of components targeted for the case. For example, for a full active CESM compset, **xxx** is cam, clm, or rtm, and so on. NNNN goes from 0001 to the number of instances of that component. (See :ref:`multiple instances<multi-instance>`) For a case with 1 instance of each component (default), NNNN will not appear in the user_nl file names. A user_nl file of a given name is created only once. Calling ``case.setup --clean`` will *not remove* any user_nl files. Changing the number of instances in the **env_mach_pes.xml** file will cause only new user_nl files to be added to ``$CASEROOT``.
software_environment.txt        This file records some aspects of the computing system on which the case is built, such as the shell environment.
=============================   ===============================================================================================================================
