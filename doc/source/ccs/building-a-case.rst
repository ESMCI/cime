.. _ccs_building_a_case:

Building a Case
===============

.. contents::
   :local:

Once the case has been created and set up, it's time to build the executable.
Several directories full of source code must be built all with the same compiler and flags.
The **case.build** script performs all build operations (setting dependencies, invoking Make/CMake,
creating the executable).

Build Process
-------------
The ``case.build`` command generates the utility, component libraries and the model executable. Each utility 
and component build has a log file generated named in the form: **$component.bldlog.$datestamp**. These are 
located in ``$EXEROOT`` which can be retrieved using ``./xmlquery EXEROOT``. If the logs are compressed 
(as indicated by a .gz file extension), the build ran successfully.

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

    ./case.build --clean

Run this to clean everything associated with the build:

::

    ./case.build --clean-all

You can also clean an individual component as shown here, where "compname" is the name of the component you want to clean (for example, atm, clm, pio, and so on).

::

    ./case.build --clean compname