.. _machine:

========================
Defining the machine
========================

CIME looks at the xml node ``MACHINE_SPEC_FILE`` in the **config_files.xml** file to identify supported out-of-the-box machines for the target model. The node has the following contents:
::

   <entry id="MACHINES_SPEC_FILE">
     <type>char</type>
     <default_value>$CIMEROOT/cime_config/$MODEL/machines/config_machines.xml</default_value>
     <group>case_last</group>
     <file>env_case.xml</file>
     <desc>file containing machine specifications for target model primary component (for documentation only - DO NOT EDIT)</desc>
     <schema>$CIMEROOT/cime_config/xml_schemas/config_machines.xsd</schema>
   </entry>

You can supplement what is in the MACHINES_SPEC_FILE by adding a config_machines.xml file to your CIME config directory.

.. _machinefile:

config_machines.xml - machine specific file
--------------------------------------------

Each ``<machine>`` tag requires the following input:

* ``DESC``: a text description of the machine
* ``NODENAME_REGEX``: a regular expression used to identify the machine. It must work on compute nodes as well as login nodes.
  | Use the ``machine`` option for **create_test** or **create_newcase** if this flag is not available.
* ``OS``: the machine's operating system
* ``PROXY``: optional http proxy for access to the internet
* ``COMPILERS``: compilers supported on the machine, in comma-separated list, default first
* ``MPILIBS``: mpilibs supported on the machine, in comma-separated list, default first
* ``PROJECT``: a project or account number used for batch jobs; can be overridden in environment or in **$HOME/.cime/config**
* ``SAVE_TIMING_DIR``: (E3SM only) target directory for archiving timing output
* ``SAVE_TIMING_DIR_PROJECTS``: (E3SM only) projects whose jobs archive timing output
* ``CIME_OUTPUT_ROOT``: Base directory for case output; the **bld** and **run** directories are written below here
* ``DIN_LOC_ROOT``: location of the input data directory
* ``DIN_LOC_ROOT_CLMFORC``: optional input location for clm forcing data
* ``DOUT_S_ROOT``: root directory of short-term archive files
* ``DOUT_L_MSROOT``: root directory on mass store system for long-term archive files
* ``BASELINE_ROOT``: root directory for system test baseline files
* ``CCSM_CPRNC``: location of the cprnc tool, which compares model output in testing
* ``GMAKE``: gnu-compatible make tool; default is "gmake"
* ``GMAKE_J``: optional number of threads to pass to the gmake flag
* ``TESTS``: (E3SM only) list of tests to run on the machine
* ``BATCH_SYSTEM``: batch system used on this machine (none is okay)
* ``SUPPORTED_BY``: contact information for support for this system
* ``MAX_TASKS_PER_NODE``: maximum number of threads/tasks per shared memory node on the machine
* ``MAX_MPITASKS_PER_NODE``: number of physical PES per shared node on the machine. In practice the MPI tasks per node will not exceed this value.
* ``PROJECT_REQUIRED``: Does this machine require a project to be specified to the batch system?
* ``mpirun``: The mpi exec to start a job on this machine.
  This is itself an element that has sub-elements that must be filled:

  * Must have a required ``<executable>`` element
  * May have optional attributes of ``compiler``, ``mpilib`` and/or ``threaded``
  * May have an optional ``<arguments>`` element which in turn contains one or more ``<arg>`` elements.
    These specify the arguments to the mpi executable and are dependent on your mpi library implementation.
  * May have an optional ``<run_exe>`` element which overrides the ``default_run_exe``
  * May have an optional ``<run_misc_suffix>`` element which overrides the ``default_run_misc_suffix``
  * May have an optional ``<aprun_mode>`` element which controls how CIME generates arguments when ``<executable>`` contains ``aprun``. 

  The ``<aprun_mode>`` element can be one of the following. The default value is ``ignore``.

  * ``ignore`` will cause CIME to ignore it's aprun module and join the values found in ``<arguments>``.
  * ``default`` will use CIME's aprun module to generate arguments.
  * ``override`` behaves the same as ``default`` expect it will use ``<arguments>`` to mutate the generated arguments. When using this mode a ``position`` attribute can be placed on ``<arg>`` tags to specify how it's used.

  The ``position`` attribute on ``<arg>`` can take one of the following values. The default value is ``per``.

  * ``global`` causes the value of the ``<arg>`` element to be used as a global argument for ``aprun``.
  * ``per`` causes the value of the ``<arg>`` element to be appended to each separate binaries arguments.

  Example using ``override``:
  ::

    <executable>aprun</executable>
    <aprun_mode>override</aprun_mode>
    <arguments>
      <arg position="global">-e DEBUG=true</arg>
      <arg>-j 20</arg>
    </arguments>

  Sample command output:
  ::

    aprun -e DEBUG=true ... -j 20 e3sm.exe : ... -j 20 e3sm.exe

* ``module_system``: How and what modules to load on this system. Module systems allow you to easily load multiple compiler environments on a machine. CIME provides support for two types of module tools: `module <http://www.tacc.utexas.edu/tacc-projects/mclay/lmod>`_ and `soft  <http://www.mcs.anl.gov/hs/software/systems/softenv/softenv-intro.html>`_. If neither of these is available on your machine, simply set ``<module_system type="none"\>``.

* ``environment_variables``: environment_variables to set on the system
   This contains sub-elements ``<env>`` with the ``name`` attribute specifying the environment variable name, and the element value specifying the corresponding environment variable value. If the element value is not set, the corresponding environment variable will be unset in your shell.

   For example, the following sets the environment variable ``OMP_STACKSIZE`` to 256M:
   ::

      <env name="OMP_STACKSIZE">256M</env>

   The following unsets this environment variable in the shell:
   ::

      <env name="OMP_STACKSIZE"></env>

   .. note:: These changes are **ONLY** activated for the CIME build and run environment, **BUT NOT** for your login shell. To activate them for your login shell, source either **$CASEROOT/.env_mach_specific.sh** or **$CASEROOT/.env_mach_specific.csh**, depending on your shell.



Batch system definition
-----------------------

CIME looks at the xml node ``BATCH_SPEC_FILE`` in the **config_files.xml** file to identify supported out-of-the-box batch system details for the target model. The node has the following contents:
::

   <entry id="BATCH_SPEC_FILE">
     <type>char</type>
     <default_value>$CIMEROOT/cime_config/$MODEL/machines/config_batch.xml</default_value>
     <group>case_last</group>
     <file>env_case.xml</file>
     <desc>file containing batch system details for target system  (for documentation only - DO NOT EDIT)</desc>
     <schema>$CIMEROOT/cime_config/xml_schemas/config_batch.xsd</schema>
   </entry>

.. _batchfile:

config_batch.xml - batch directives
-------------------------------------------------

The **config_batch.xml** schema is defined in **$CIMEROOT/config/xml_schemas/config_batch.xsd**.

CIME supports these batch systems: pbs, cobalt, lsf and slurm.

The entries in **config_batch.xml** are hierarchical.

#. General configurations for each system are provided at the top of the file.

#. Specific modifications for a given machine are provided below.  In particular each machine should define its own queues.

#. Following is a machine-specific queue section.  This section details the parameters for each queue on the target machine.

#. The last section describes several things:

   - each job that will be submitted to the queue for a CIME workflow,

   - the template file that will be used to generate that job,

   - the prerequisites that must be met before the job is submitted, and

   - the dependencies that must be satisfied before the job is run.

By default the CIME workflow consists of two jobs (**case.run**, **case.st_archive**).

In addition, there is **case.test** job that is used by the CIME system test workflow.


.. _defining-compiler-settings:

Compiler settings
-----------------

CIME looks at the xml element ``CMAKE_MACROS_DIR`` in the **config_files.xml** file to identify supported out-of-the-box compiler details for the target model. The node has the following contents:
::

  <entry id="CMAKE_MACROS_DIR">
    <type>char</type>
    <default_value>$CIMEROOT/config/$MODEL/machines/cmake_macros</default_value>
    <group>case_last</group>
    <file>env_case.xml</file>
    <desc>Directory containing cmake macros (for documentation only - DO NOT EDIT)</desc>
  </entry>

Additional compilers are made avilable by adding cmake macros files to the directory pointed to by CMAKE_MACROS_DIR or to your $HOME/.cime directory.

.. _compilerfile:

config_compilers.xml - compiler paths and options **DEPRECATED use cmake_macros**
-------------------------------------------------
The **config_compilers.xml** file defines compiler flags for building CIME (and also CESM and E3SM prognostic CIME-driven components).

#. General compiler flags (e.g., for the gnu compiler) that are machine- and componen-independent are listed first.

#. Compiler flags specific to a particular operating system are listed next.

#. Compiler flags that are specific to particular machines are listed next.

#. Compiler flags that are specific to particular CIME-driven components are listed last.

The order of listing is a convention and not a requirement.

The possible elements and attributes that can exist in the file are documented in **$CIME/config/xml_schemas/config_compilers_v2.xsd**.

To clarify several conventions:

- The ``<append>`` element implies that any previous definition of that element's parent will be appended with the new element value.
  As an example, the following entry in **config_compilers.xml** would append the value of ``CPPDEFS`` with ``-D $OS`` where ``$OS`` is the environment value of ``OS``.

  ::

     <compiler>
        <CPPDEFS>
            <append> -D<env>OS</env> </append>
        </CPPDEFS>
     </compiler>

- The ``<base>`` element overwrites its parent element's value. For example, the following entry would overwrite the ``CONFIG_ARGS`` for machine ``melvin`` with a ``gnu`` compiler to be ``--host=Linux``.

  ::

     <compiler MACH="melvin" COMPILER="gnu">
        <CONFIG_ARGS>
           <base> --host=Linux </base>
        </CONFIG_ARGS>
     </compiler>
