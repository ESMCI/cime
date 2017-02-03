.. _building-a-case:

Building a Case
========================

The following summarizes details of building the model exectuable.

How do I build my model?
------------------------

After calling **case.setup**, you can build the model executable by running **./$CASE.build**. Running this will:

1. Create the component namelists in ``$RUNDIR`` (by calling the ``Buildconf/$component.buildnml.csh`` scripts).
2. Check for the `required input data sets <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and download missing data automatically on local disk, and if successful proceed to the following steps.
3. Create the necessary utility libraries for ``mct``, ``pio``, ``gptl`` and ``csm_share``. 
   These will be placed in ``$EXEROOT/bld/lib``.
4. Create the necessary component libraries.
   These will also be placed in ``$EXEROOT/bld/lib``.
5. Create the model executable (either ``cesm.exe`` or ``acme.exe``). 
   This will be placed in ``$EXEROOT``.

``$CASEROOT/Tools/Makefile`` and ``$CASEROOT/Macros.make`` are used to generate the utility libraries, the component libraries and the model executable. 
You do not need to change the default build settings to create the executable. 
However, since the CIME scripts provide you with a great deal of flexibility in customizing various aspects of the build process, it is useful to become familiar with these in order to make optimal use of the system.

The `env_build.xml variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, control various aspects of building the model executable. 
Most of the variables should not be modified by users. Among the variables that you can modify are ``BUILD_THREADED``, ``DEBUG`` and ``GMAKE_J``. 
Full documentation for each variable is provided in the `env_build.xml variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.
::

   > cd $CASEROOT
   > ./$CASE.build

Diagnostic comments will appear as the build proceeds.
You will also be notified that the required case input data in ``$DIN_LOC_ROOT`` has been successfully checked.

Finally, the build script generates the utility and component libraries and the model executable. 
Build log files are created as the model build proceeds. 
Each is date stamped, and a pointer to the build log file for that library or component is shown. 
The build log files have names of the form $model.bldlog.$datestamp and are located in ``$BLDDIR``. 
If they are compressed (indicated by a .gz file extension), then the build ran successfully.

Invoking **$CASE.build** creates the following directory structure in ``$EXEROOT`` if the ``intel`` compiler is used:
::

   atm/, cpl/, esp/, glc/, ice/, intel/, lib/, lnd/, ocn/, rof/, wav/

All of the above directories, other than ``intel/`` and ``lib/``, each contain an ``obj/`` directory where the compiled object files for the target model component is placed. 
These object files are collected into libraries that are placed in ``lib/`` along with the ``mct``, ``pio``, ``gptl``, and ``csm_share`` libraries. 
Special include modules are also placed in ``lib/include``. The model executable (either ``cesm.exe`` or ``acme.exe``) is placed directly in ``$EXEROOT``. 
On the other hand, component namelists, component logs, output datasets, and restart files are placed in ``$RUNDIR``. 
It is important to note that ``$RUNDIR`` and ``$EXEROOT`` are independent variables which are set ``$CASEROOT/env_run.xml``.

All active and data components use input datasets. 
A local disk needs ``$DIN_LOC_ROOT`` to be populated with input data in order to run CIME and the CIME complaint prognostic components. 
Input data is provided as part of the CIME release via data from the subversion input data server. 
However, on supported machines (and some non-supported machines), data already exists in the default local filesystem input data area as specified by ``$DIN_LOC_ROOT`` (see below).

Input data is handled by the build process as follows:

- The buildnml scripts in ``Buildconf/`` create listings of required component input datasets in the ``Buildconf/$component.input_data_list`` files.

- ``$CASE.build`` checks for the presence of the required input data files in the root directory ``$DIN_LOC_ROOT``. If all required data sets are found on local disk, then the build can proceed.

- If any of the required input data sets are not found, the build script will abort and the files that are missing will be listed. At this point, you must obtain the required data from the input data server using check_input_data with the -export option.

The ``env_run.xml`` variables ``DIN_LOC_ROOT`` and ``DIN_LOC_ROOT_CLMFORC`` determine where you should expect input data to reside on local disk. See the `input data variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

Input Data
-----------------------

User-created input data
^^^^^^^^^^^^^^^^^^^^^^^

If you want to use new user-created dataset(s) and give these dataset(s) names that are different than the names in ``$DIN_LOC_ROOT``, we recommend using the script **link_dirtree** in the directory ``$CCSMROOT/scripts``. **link_dirtree** creates a virtual copy of the input data directory by linking one directory tree to another. The full directory structure of the original directory is duplicated and the files are linked. To use this script, use the -h optiion for usage.
```
> cd $CCSMROOT/scripts 
> ./link_dirtree -h
```
**link_dirtree** can be conveniently used to generate the equivalent of a local copy of ``$DIN_LOC_ROOT`` which can then be populated with user-specified input datasets. For example, you can first generate a virtual copy of ``$DIN_LOC_ROOT`` in /user/home/newdata with the following command:
```
> link_dirtree $DIN_LOC_ROOT /user/home/newdata
```
then incorporate the new dataset(s) directly into the appropriate directory in /user/home/newdata.

Using the input data server
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script ``$CASEROOT/check_input_data`` determines if the required data files for the case exist on local disk in the appropriate subdirectory of ``$DIN_LOC_ROOT``. If any of the required datasets do not exist locally, **check_input_data** provides the capability for downloading them to the ``$DIN_LOC_ROOT`` directory hierarchy via interaction with the input data server. You can independently verify that the required data is present locally by using the following commands:
```
> cd $CASEROOT
> check_input_data -help
> check_input_data -inputdata $DIN_LOC_ROOT -check
```
If input data sets are missing, you must obtain the datasets from the input data server:
```
> cd $CASEROOT
> check_input_data -inputdata $DIN_LOC_ROOT -export
``
Required data files not on local disk will be downloaded through interaction with the Subversion input data server. These will be placed in the appropriate subdirectory of ``$DIN_LOC_ROOT``. For what to expect when interacting with a Subversion repository, see `downloading input data <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

Rebuilding the model
^^^^^^^^^^^^^^^^^^^^

You should rebuild the model under the following circumstances:

If either ``env_build.xml`` or ``Macros`` has been modified, and/or if code is added to ``SourceMods/src.*``, then it's safest to clean the build and rebuild from scratch as follows,
::

   > cd $CASEROOT
   > ./case.build --clean 

If you have ONLY modified the PE layout in ``env_mach_pes.xml`` (see `setting the PE layout <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_) then it's possible that a clean is not required.
::

   > cd $CASEROOT
   > ./case.build

But if the threading has been turned on or off in any component relative to the previous build, then the build script should fail with the following error
::

   ERROR SMP STATUS HAS CHANGED
   SMP_BUILD = a0l0i0o0g0c0
   SMP_VALUE = a1l0i0o0g0c0
   A manual clean of your obj directories is strongly recommended
   You should execute the following:
      ./case.build --clean
      ./case.build
    
    ---- OR ----
    You can override this error message at your own risk by executing
      ./xmlchange SMP_BUILD=0 
    Then rerun the build script interactively

and suggest that the model be rebuilt from scratch.

You are responsible for manually rebuilding the model when needed. If there is any doubt, you should rebuild.
