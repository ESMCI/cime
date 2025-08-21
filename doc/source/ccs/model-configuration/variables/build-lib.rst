.. _model_config_build_lib:

CASE_SUPPORT_LIBRARIES
==============

.. contents::
    :local:

Overview
--------
This variable is a list of support libraries that should be built by the case.
It is defined by the driver and component buildnml scripts and is used with BUILD_LIB_FILE to
locate required buildlib scripts.  It is a list of libraries which will be built in list order so
it is important that dependent libraries are identified.

Entry
-----
The CASE_SUPPORT_LIBRARIES variable should be defined in the drivers config_component.xml file as

.. code-block:: xml

   <entry id="CASE_SUPPORT_LIBRARIES">
     <type>char</type>
     <default_value></default_value>
     <group>build_def</group>
     <file>env_build.xml</file>
     <desc>Support libraries required</desc>
   </entry>

BUILD_LIB_FILE
==============

Overview
--------
This variable defines the paths to library build scripts. A description of the scripts
themselves can be found below.

Entry
-----
The following is an exmple entry for ``BUILD_LIB_FILE`` in ``config_files.xml``.

Each ``value`` corresponds to a library that can be built. The ``lib`` attribute is the name of the library and the ``value`` is the path to the buildlib script.

.. code-block:: xml

    <entry id="BUILD_LIB_FILE">
        <type>char</type>
        <values>
            <value lib="kokkos">$SRCROOT/share/build/buildlib.kokkos</value>
            <value lib="gptl">$SRCROOT/share/build/buildlib.gptl</value>
            <value lib="pio">$CIMEROOT/CIME/build_scripts/buildlib.pio</value>
            <value lib="spio">$SRCROOT/share/build/buildlib.spio</value>
            <value lib="mct">$SRCROOT/share/build/buildlib.mct</value>
            <value lib="csm_share">$SRCROOT/share/build/buildlib.csm_share</value>
            <value lib="mpi-serial">$SRCROOT/share/build/buildlib.mpi-serial</value>
            <value lib="cprnc">$CIMEROOT/CIME/build_scripts/buildlib.cprnc</value>
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc> path to buildlib script for the given library </desc>
    </entry>


Build library
--------------
The ``buildnml`` script for a given component can modify the case variable ``CASE_SUPPORT_LIBRARIES`` and add a list of libraries needed by the given component, the list should be in order of dependancies with dependent libraries listed after those they depend upon.  

Implementing a ``buildlib`` for a component is as simple as creating a python file and defining a single function; *buildlib*.

Below are the arguments for the ``buildlib`` function.

+-------------+------------------------------------------+
| Parameter   | Description                              |
+=============+==========================================+
| bldroot     | The root directory to build the library. |
+-------------+------------------------------------------+
| installpath | The directory to install the library.    |
+-------------+------------------------------------------+
| case        | This is a CIME.case.case.Case object.    |
+-------------+------------------------------------------+

Use this function to setup, build the library and run any post-processing after the build.

.. note::

    It's best to start by copying a `buildlib` from another component for a stating point.

Example
```````

.. code-block:: python
    
    import glob

    from CIME.utils import copyifnewer, run_bld_cmd_ensure_logging
    from CIME.build import get_standard_cmake_args

    def buildlib(bldroot, installpath, case):
        paths = glob.glob(...)

        for x in paths:
            copyifnewer(x, os.path.join(...))

        libdir = os.path.join(...)

        cmake_args = get_standard_cmake_args(case, installpath)

        run_bld_cmd_ensure_logging(f"cmake {cmake_args}", logger, from_dir=libdir)
