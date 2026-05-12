.. _ccs_building_a_case:

Building a Case
===============

.. contents::
   :local:

Once the case has been created and set up, it's time to build the executable.
Several directories full of source code must be built all with the same compiler and flags.
The **case.build** script performs all build operations (setting dependencies, invoking Make/CMake,
creating the executable).

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
Running ``case.build`` will:

1. Create the component namelists in ``$RUNDIR`` and ``$CASEROOT/CaseDocs``.
2. Build the shared libraries, utilities (e.g. ``cprnc``) and place them in ``$SHAREDLIBROOT``.
3. Build the components and model executables, which is placed in ``$EXEROOT``.

Each utility, component, and the model will generate a log file in the form ``$name.bldlog.$datestamp`` in the ``$EXEROOT`` directory.
If the logs are compressed (as indicated by a .gz file extension), the build ran successfully.

.. note::

    The following is just an example and can vary based on the model, compiler, and compset.

Running ``case.build`` typically results in a directory structure similar to the following in ``$EXEROOT``.

.. code-block:: shell

    .
    ├── atm
    │   └── obj
    ├── cpl
    │   └── obj
    ├── esp
    │   └── obj
    ├── glc
    │   └── obj
    ├── iac
    │   └── obj
    ├── ice
    │   └── obj
    ├── lib
    │   └── include
    ├── lnd
    │   └── obj
    ├── ocn
    │   └── obj
    ├── oneapi-ifx
    │   └── mpich
    │       └── nodebug
    │           └── nothreads
    │               ├── gptl
    │               ├── include
    │               ├── lib
    │               ├── mct
    │               └── spio
    ├── rof
    │   └── obj
    └── wav
        └── obj

In this example, the model is built with the Intel oneAPI compiler and uses MPICH for parallel communication (denoted by the ``oneapi-ifx`` and ``mpich`` directories). The ``nodebug`` and ``nothreads`` directories indicate that the build is not using debugging flags or threading.

The directories under ``oneapi-ifx/mpich/nodebug/nothreads`` contains the external libraries used by the model.

The ``lib/include`` directory contains special include modules.

The model executable is placed directly in the ``$EXEROOT`` directory, which is typically named after the model (e.g., **cesm.exe** or **e3sm.exe**).

In the ``$EXEROOT`` directory is where you'll find the build logs for each component, external library, and the model executable.

Component namelists, component logs, output data sets, and restart files are placed in ``$RUNDIR``.

.. important::

    It is important to note that ``$RUNDIR`` and ``$EXEROOT`` are independent variables that are set in the ``$CASEROOT/env_run.xml`` file.

    The default values for ``$RUNDIR`` and ``$EXEROOT`` respectively are ``$CIME_OUTPUT_ROOT/$CASE/run`` and ``$CIME_OUTPUT_ROOT/$CASE/bld``. Changing the ``$CIME_OUTPUT_ROOT`` variable will change the location of the run and build directories.

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