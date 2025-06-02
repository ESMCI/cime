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

Configure model components
--------------------------
CIME-compilant components primarily use Fortran namelists to control runtime options.  Some components use
other text-based files for runtime options.

All CIME-compliant components generate their input variable files using a ``buildnml`` script typically located in the
component's ``cime_config`` directory (or other location as set in ``config_file.xml``).
The ``buildnml`` may call other scripts to complete the construction of the input file.

For example, if a model's atmosphere model (DATM) was located in the directory ``$SRCROOT/components/data_comps/datm``, the
``buildnml`` script would be located in ``$SRCROOT/components/data_comps/datm/cime_config/buildnml``.

Users can customize a component models's namelist in two ways:

1. By editing the ``$CASEROOT/user_nl_<comp>`` files

  These files should be modified via keyword-value pairs that correspond to new namelist or input data settings.  They use the
  syntax of Fortran namelists.

2. By calling ``xmlchange`` to modify xml variables in your ``$CASEROOT``.

   Many of these variables are converted to Fortran namelist values for input by the models.  Variables that have
   to be coordinated between models in a coupled system (such as how many steps to run for) are usually in a CIME xml file.

You can generate the component namelists by running ``preview_namelists`` from ``$CASEROOT`` which will output the namelists to
``$CASEROOT/CaseDocs/``.  This is useful for checking the values of the namelists before running the model.

.. warning::

    The namelist files in ``CaseDocs`` are there only for user reference and **SHOULD NOT BE EDITED** since they are overwritten every time ``preview_namelists`` and ``case.submit`` are called and the files read at runtime are not the ones in ``CaseDocs``.

Customizing driver input variables
----------------------------------
The driver input namelists/variables are contained in the following files:

* drv_in
* drv_flds_in
* seq_maps.rc

.. warning::

      The ``seq_maps.rc`` file has a different file format from Fortran namelists.

All driver/coupler namelist variables are defined in ``namelist_definition_drv.xml`` located in the ``cime_config`` directory of the driver source code.
If a variable can be modified it will have the ``modify_via_xml`` attribute set to ``xml_variable_name`` which can be modified by calling ``xmlchange``.
All other variables must be modified by adding a keyword value pair at the end of ``user_nl_cpl``.
For example, to change the driver namelist value of ``eps_frac`` to ``1.0e-15``, add the following line to the end of the ``user_nl_cpl``:

::

   eps_frac = 1.0e-15

On the hand, to change the driver namelist value of the starting year/month/day, ``start_ymd`` to ``18500901``, use the command:

::

   ./xmlchange RUN_STARTDATE=1850-09-01

.. note::

      To see the result of a change, call ``preview_namelists`` and verify that the new value appears in ``$CASEROOT/CaseDocs/drv_in``.

Customizing data model input variable and stream files
------------------------------------------------------

Each data model can be runtime-configured with its own namelist.

Data Atmosphere (DATM)
``````````````````````

DATM can be user-customized by changing either its  *namelist input files* or its *stream files*.
The namelist file for DATM is **datm_in** (or **datm_in_NNN** for multiple instances).

- To modify **datm_in** or **datm_in_NNN**, add the appropriate keyword/value pair(s) for the namelist changes that you want at the end of the **user_nl_datm** file or the **user_nl_datm_NNN** file in ``$CASEROOT``.

- To modify the contents of a DATM stream file, first run ``preview_namelists`` to list the *streams.txt* files in the **CaseDocs/** directory. Then, in the same directory:

  1. Make a *copy* of the file with the string *"user_"* prepended.
        ``> cp datm.streams.txt.[extension] user_datm.streams.txt[extension.``
  2. **Change the permissions of the file to be writeable.** (chmod 644)
        ``chmod 644 user_datm.streams.txt[extension``
  3. Edit the **user_datm.streams.txt.*** file.

**Example**

If the stream txt file is **datm.streams.txt.CORE2_NYF.GISS**, the modified copy should be **user_datm.streams.txt.CORE2_NYF.GISS**.
After calling ``preview_namelists`` again, your edits should appear in **CaseDocs/datm.streams.txt.CORE2_NYF.GISS**.

Data Ocean (DOCN)
`````````````````

DOCN can be user-customized by changing either its namelist input or its stream files.
The namelist file for DOCN is **docn_in** (or **docn_in_NNN** for multiple instances).

- To modify **docn_in** or **docn_in_NNN**, add the appropriate keyword/value pair(s) for the namelist changes that you want at the end of the file in ``$CASEROOT``.

- To modify the contents of a DOCN stream file, first run ``preview_namelists`` to list the *streams.txt* files in the **CaseDocs/** directory. Then, in the same directory:

  1. Make a *copy* of the file with the string *"user_"* prepended.
        ``> cp docn.streams.txt.[extension] user_docn.streams.txt[extension.``
  2. **Change the permissions of the file to be writeable.** (chmod 644)
        ``chmod 644 user_docn.streams.txt[extension``
  3. Edit the **user_docn.streams.txt.*** file.

**Example**

As an example, if the stream text file is **docn.stream.txt.prescribed**, the modified copy should be **user_docn.streams.txt.prescribed**.
After changing this file and calling ``preview_namelists`` again, your edits should appear in **CaseDocs/docn.streams.txt.prescribed**.

Data Sea-ice (DICE)
```````````````````

DICE can be user-customized by changing either its namelist input or its stream files.
The namelist file for DICE is ``dice_in`` (or ``dice_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_dice`` (or ``user_nl_dice_NNN`` for multiple instances).

- To modify **dice_in** or **dice_in_NNN**, add the appropriate keyword/value pair(s) for the namelist changes that you want at the end of the file in ``$CASEROOT``.

- To modify the contents of a DICE stream file, first run ``preview_namelists`` to list the *streams.txt* files in the **CaseDocs/** directory. Then, in the same directory:

  1. Make a *copy* of the file with the string *"user_"* prepended.
        ``> cp dice.streams.txt.[extension] user_dice.streams.txt[extension.``
  2. **Change the permissions of the file to be writeable.** (chmod 644)
        ``chmod 644 user_dice.streams.txt[extension``
  3. Edit the **user_dice.streams.txt.*** file.

Data Land (DLND)
````````````````

DLND can be user-customized by changing either its namelist input or its stream files.
The namelist file for DLND is ``dlnd_in`` (or ``dlnd_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_dlnd`` (or ``user_nl_dlnd_NNN`` for multiple instances).

- To modify **dlnd_in** or **dlnd_in_NNN**, add the appropriate keyword/value pair(s) for the namelist changes that you want at the end of the file in ``$CASEROOT``.

- To modify the contents of a DLND stream file, first run ``preview_namelists`` to list the *streams.txt* files in the **CaseDocs/** directory. Then, in the same directory:

  1. Make a *copy* of the file with the string *"user_"* prepended.
        ``> cp dlnd.streams.txt.[extension] user_dlnd.streams.txt[extension.``
  2. **Change the permissions of the file to be writeable.** (chmod 644)
        ``chmod 644 user_dlnd.streams.txt[extension``
  3. Edit the **user_dlnd.streams.txt.*** file.

Data River (DROF)
`````````````````

DROF can be user-customized by changing either its namelist input or its stream files.
The namelist file for DROF is ``drof_in`` (or ``drof_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_drof`` (or ``user_nl_drof_NNN`` for multiple instances).

- To modify **drof_in** or **drof_in_NNN**, add the appropriate keyword/value pair(s) for the namelist changes that you want at the end of the file in ``$CASEROOT``.

- To modify the contents of a DROF stream file, first run ``preview_namelists`` to list the *streams.txt* files in the **CaseDocs/** directory. Then, in the same directory:

  1. Make a *copy* of the file with the string *"user_"* prepended.
        ``> cp drof.streams.txt.[extension] user_drof.streams.txt[extension.``
  2. **Change the permissions of the file to be writeable.** (chmod 644)
        ``chmod 644 user_drof.streams.txt[extension``
  3. Edit the **user_drof.streams.txt.*** file.

.. TODO:: remove cesm specific docs

Customizing CESM active component-specific namelist settings
------------------------------------------------------------

CAM
```

CIME calls **$SRCROOT/components/cam/cime_config/buildnml** to generate the CAM's namelist variables.

CAM-specific CIME xml variables are set in **$SRCROOT/components/cam/cime_config/config_component.xml** and are used by CAM's **buildnml** script to generate the namelist.

For complete documentation of namelist settings, see `CAM namelist variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/cam_nml.html>`_.

To modify CAM namelist settings, add the appropriate keyword/value pair at the end of the **$CASEROOT/user_nl_cam** file. (See the documentation for each file at the top of that file.)

For example, to change the solar constant to 1363.27, modify **user_nl_cam** file to contain the following line at the end:
::

 solar_const=1363.27

To see the result, call ``preview_namelists`` and verify that the new value appears in **CaseDocs/atm_in**.

CLM
```

CIME calls **$SRCROOT/components/clm/cime_config/buildnml** to generate the CLM namelist variables.

CLM-specific CIME xml variables are set in **$SRCROOT/components/clm/cime_config/config_component.xml** and are used by CLM's **buildnml** script to generate the namelist.

For complete documentation of namelist settings, see `CLM namelist variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/clm5_0_nml.html>`_.

To modify CLM namelist settings, add the appropriate keyword/value pair at the end of the **$CASEROOT/user_nl_clm** file.

To see the result, call ``preview_namelists`` and verify that the changes appear correctly in **CaseDocs/lnd_in**.

MOSART
``````

CIME calls **$SRCROOT/components/mosart/cime_config/buildnml** to generate the MOSART namelist variables.

To modify MOSART namelist settings, add the appropriate keyword/value pair at the end of the **$CASEROOT/user_nl_rtm** file.

To see the result of your change, call ``preview_namelists`` and verify that the changes appear correctly in **CaseDocs/rof_in**.

CICE
````

CIME calls **$SRCROOT/components/cice/cime_config/buildnml** to generate the CICE namelist variables.

For complete documentation of namelist settings, see `CICE namelist variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/cice_nml.html>`_.

To modify CICE namelist settings, add the appropriate keyword/value pair at the end of the **$CASEROOT/user_nl_cice** file.
(See the documentation for each file at the top of that file.)
To see the result of your change, call ``preview_namelists`` and verify that the changes appear correctly in **CaseDocs/ice_in**.

In addition, ``case.setup`` creates CICE's compile time `block decomposition variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/cice_input.html>`_ in **env_build.xml**.

POP2
````

CIME calls **$SRCROOT/components/pop2/cime_config/buildnml** to generate the POP2 namelist variables.

For complete documentation of namelist settings, see `POP2 namelist variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/pop2_nml.html>`_.

To modify POP2 namelist settings, add the appropriate keyword/value pair at the end of the **$CASEROOT/user_nl_pop2** file.
(See the documentation for each file at the top of that file.)
To see the result of your change, call ``preview_namelists`` and verify that the changes appear correctly in **CaseDocs/ocn_in**.

CISM
````

See `CISM namelist variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/cism_nml.html>`_ for a complete description of the CISM runtime namelist variables. This includes variables that appear both in **cism_in** and in **cism.config**.

To modify any of these settings, add the appropriate keyword/value pair at the end of the **user_nl_cism** file. (See the documentation for each file at the top of that file.)
Note that there is no distinction between variables that will appear in **cism_in** and those that will appear in **cism.config**: simply add a new variable setting in **user_nl_cism**, and it will be added to the appropriate place in **cism_in** or **cism.config**.
To see the result of your change, call ``preview_namelists`` and verify that the changes appear correctly in **CaseDocs/cism_in** and **CaseDocs/cism.config**.

Some CISM runtime settings are sets via **env_run.xml**, as documented in `CISM runtime variables <https://www.cesm.ucar.edu/models/cesm2/settings/current/cism_input.html>`_.

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
user_nl_xxx[_NNNN]              Files where all user modifications to component namelists are made. **xxx** is any one of the set of components targeted for the case. For example, for a full active CESM compset, **xxx** is cam, clm, or rtm, and so on. NNNN goes from 0001 to the number of instances of that component. (See :ref:`multiple instances<ccs-examples-multi-instance>`) For a case with 1 instance of each component (default), NNNN will not appear in the user_nl file names. A user_nl file of a given name is created only once. Calling ``case.setup --clean`` will *not remove* any user_nl files. Changing the number of instances in the **env_mach_pes.xml** file will cause only new user_nl files to be added to ``$CASEROOT``.
software_environment.txt        This file records some aspects of the computing system on which the case is built, such as the shell environment.
=============================   ===============================================================================================================================
