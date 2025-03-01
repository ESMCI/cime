.. _ccs_building_a_case:

Building a Case
===============

.. contents::
   :local:

Once the case has been created and set up, it's time to build the executable.
Several directories full of source code must be built all with the same compiler and flags.
**case.build** performs all build operations (setting dependencies, invoking Make/CMake,
creating the executable).

Build Process
-------------
The ``case.build`` command generates the utility/component libraries and the model executable. Each utility and component build has a log file generated named in the form: **$component.bldlog.$datestamp**. They are located in ``$BLDDIR``. If they are compressed (as indicated by a .gz file extension), the build ran successfully.

Invoking ``case.build`` creates the following directory structure in ``$EXEROOT`` if the Intel compiler is used:

::

    atm/
    cpl/
    esp/
    glc/
    ice/
    intel/
    lib/
    lnd/
    ocn/
    rof/
    wav/

Except for **intel/** and **lib/**, each directory contains an **obj/** subdirectory for the target model component's compiled object files.

The *mct*, *pio*, *gptl*, and *csm_share* libraries are placed in a directory tree that reflects their dependencies. See the **bldlog** for a given component to locate the library.

Special **include** modules are placed in **lib/include**. The model executable (**cesm.exe** or **e3sm.exe**, for example) is placed directly in ``$EXEROOT``.

Component namelists, component logs, output data sets, and restart files are placed in ``$RUNDIR``.

.. important::

    It is important to note that ``$RUNDIR`` and ``$EXEROOT`` are independent variables that are set in the ``$CASEROOT/env_run.xml`` file.

    The default values for ``$RUNDIR`` and ``$EXEROOT`` respectively are ``$CIME_OUTPUT_ROOT/$CASE/run`` and ``$CIME_OUTPUT_ROOT/$CASE/bld``. Changing the ``$CIME_OUTPUT_ROOT`` variable will change the location of the run and build directories.

Configuring the Build
---------------------
You do not need to change the default build settings to create the executable, but it may be useful to change them to make optimal use of the system. CIME provides the :ref:`xmlquery <ccs_xmlquery>` and :ref:`xmlchange <ccs_xmlchange>` commands to view and modify the build settings.

Below are some variables that affect the build process and output.

+------------------+-----------------------------------------------------------+
| Variable         | Description                                               |
+==================+===========================================================+
| BUILD_THREADED   | If ``TRUE`` the model will be built with OpenMP.          |
+------------------+-----------------------------------------------------------+
| DEBUG            | If ``TRUE`` the model is compiled with debugging instead  |
|                  | of optimization flags.                                    |
+------------------+-----------------------------------------------------------+
| GMAKE_J          | The number of threads GNU Make should use while building. |
+------------------+-----------------------------------------------------------+

Building the Model
------------------
After calling ``case.setup``, running ``case.build`` will:

1. Create the component namelists in ``$RUNDIR`` and ``$CASEROOT/CaseDocs``.
2. Create the necessary compiled libraries used by coupler and component models ``mct``, ``pio``, ``gptl``, and ``csm_share``.
   The libraries will be placed in a path below ``$SHAREDLIBROOT``.
3. Create the necessary compiled libraries for each component model. These are placed in ``$EXEROOT/bld/lib``.
4. Create the model executable ``$MODEL.exe``, which is placed in ``$EXEROOT``.

Rebuilding the Model
--------------------
The model will need to be rebuilt if any of the following is changed:

* ``env_build.xml`` is modified
* ``Macros.make`` is modified
* Code is added to ``SourceMods/src``

.. note::

    ``Macros.make`` may or may not be present. It's dependent on the model and whether Make or CMake is used.

It's safest to clean the build and rebuild from scratch in these cases.

.. code-block:: bash

    ./case.build --clean-all
    ./case.build

If threading has been changed (turned on or off) in any component since the previous build, the build script should fail with the following error and suggestion that the model be rebuilt from scratch:

::

    ERROR SMP STATUS HAS CHANGED
    SMP_BUILD = a0l0i0o0g0c0
    SMP_VALUE = a1l0i0o0g0c0
    A manual clean of your obj directories is strongly recommended.
    You should execute the following:
      ./case.build --clean
      ./case.build

    ---- OR ----

    You can override this error message at your own risk by executing:
      ./xmlchange SMP_BUILD=0
    Then rerun the build script interactively.

.. important::

    If there is any doubt, rebuild.

Run this to clean all of the model components (except for support libraries such as **mct** and **gptl**):

::

    case.build --clean

Run this to clean everything associated with the build:

::

    case.build --clean-all

You can also clean an individual component as shown here, where "compname" is the name of the component you want to clean (for example, atm, clm, pio, and so on).

::

    case.build --clean compname

.. _inputdata:

Input Data
----------
All active components and data components use input data sets. In order to run CIME and the CIME-compliant active components, a local disk needs the directory tree that is specified by the XML variable ``$DIN_LOC_ROOT`` to be populated with input data.

Input data is provided by various servers configured in the model's CIME configuration. It is downloaded from the server on an as-needed basis determined by the case. Data may already exist in the default local file system's input data area as specified by ``$DIN_LOC_ROOT``.

Input data can occupy significant space on a system, so users should share a common ``$DIN_LOC_ROOT`` directory on each system if possible.

The build process handles input data as follows:

* The **buildnml** scripts in the various component ``cime_config`` directories create listings of required component input data sets in the ``Buildconf/$component.input_data_list`` files.
* ``check_input_data``, which is called by ``case.build``, checks for the presence of the required input data files in the root directory ``$DIN_LOC_ROOT``.
* If all required data sets are found on the local disk, the build can proceed.
* If any of the required input data sets are not found locally, the files that are missing are listed. At this point, you must obtain the required data from the input data server with ``check_input_data`` as shown here:

    ::

        check_input_data --download

The **env_run.xml** variables ``$DIN_LOC_ROOT`` and ``$DIN_LOC_ROOT_CLMFORC`` determine where you should expect input data to reside on a local disk.
