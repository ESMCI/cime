.. _model_config_machines:

MACHINE_SPEC_FILE
==================

.. contents::
  :local:

Overview
--------
CIME looks at the XML node ``MACHINE_SPEC_FILE`` in the **config_files.xml** file to identify supported out-of-the-box machines for the target model. The node has the following contents:

Entry
-----
The following is an entry for ``MACHINES_SPEC_FILE`` in ``config_files.xml``.

Only a single value is required.

.. code-block:: xml

    <entry id="MACHINES_SPEC_FILE">
            <type>char</type>
            <default_value>$SRCROOT/cime_config/machines/config_machines.xml</default_value>
            <group>case_last</group>
            <file>env_case.xml</file>
            <desc>File containing machine specifications for the target model primary component (for documentation only - DO NOT EDIT)</desc>
            <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_machines.xsd</schema>
    </entry>

You can supplement what is in the MACHINES_SPEC_FILE by adding a config_machines.xml file to your CIME config directory.

.. _model_config_machines_def:

Contents
--------

Schema Definition
`````````````````

Version 3
:::::::::
The following is an example of a version 3.0 ``config_machines.xml`` file. Version 3.0 breaks machine definitions into separate directories.

.. code-block:: xml

  <config_machines version="3.0">
    <NODENAME_REGEX>
      <value MACH="docker">docker</value>
      ...
    </NODENAME_REGEX>

    <default_run_suffix>
      ...
    </default_run_suffix>
  </config_machines>

For each ``NODENAME_REGEX`` entry, there should be a directory named by the value of the ``MACH`` attribute.

In these directories is where the machines ``config_machines.xml``, ``config_batch.xml``, and ``.*.cmake`` are stored.

The ``config_machines.xml`` XML will only contain the ``machine`` portion and will omit the ``NODENAME_REGEX`` element.

Version 2
`````````
The following is an example of a version 2.0 ``config_machines.xml`` file. This format provides a monolithic file for all machine definitions.

.. code-block:: xml

  <config_machines version="2.0">
        <machine MACH="docker">
                <DESC>Docker</DESC>
                <OS>LINUX</OS>
                <PROXY />
                <COMPILERS>gnu,gnuX</COMPILERS>
                <MPILIBS>openmpi</MPILIBS>
                <PROJECT>CIME</PROJECT>
                <SAVE_TIMING_DIR>/storage/timings</SAVE_TIMING_DIR>
                <SAVE_TIMING_DIR_PROJECTS>CIME</SAVE_TIMING_DIR_PROJECTS>
                <CIME_OUTPUT_ROOT>/storage/cases</CIME_OUTPUT_ROOT>
                <DIN_LOC_ROOT>/storage/inputdata</DIN_LOC_ROOT>
                <DIN_LOC_ROOT_CLMFORC>/storage/inputdata-clmforc</DIN_LOC_ROOT_CLMFORC>
                <DOUT_S_ROOT>/storage/archive/$CASE</DOUT_S_ROOT>
                <BASELINE_ROOT>/storage/baselines/$COMPILER</BASELINE_ROOT>
                <CCSM_CPRNC>/storage/tools/cprnc</CCSM_CPRNC>
                <GMAKE>make</GMAKE>
                <GMAKE_J>4</GMAKE_J>
                <TESTS>e3sm_developer</TESTS>
                <BATCH_SYSTEM>none</BATCH_SYSTEM>
                <SUPPORTED_BY>boutte3@llnl.gov</SUPPORTED_BY>
                <MAX_TASKS_PER_NODE>8</MAX_TASKS_PER_NODE>
                <MAX_MPITASKS_PER_NODE>8</MAX_MPITASKS_PER_NODE>
                <mpirun mpilib="openmpi">
                <executable>mpiexec</executable>
                <arguments>
                        <arg name="ntasks">-n {{ total_tasks }}</arg>
                        <arg name="oversubscribe">--oversubscribe</arg>
                </arguments>
                </mpirun>
                <module_system type="none" />
                <RUNDIR>$CASEROOT/run</RUNDIR>
                <EXEROOT>$CASEROOT/bld</EXEROOT>
                <environment_variables>
                        <env name="OMPI_ALLOW_RUN_AS_ROOT">1</env>
                        <env name="OMPI_ALLOW_RUN_AS_ROOT_CONFIRM">1</env>
                        <env name="NETCDF_C_PATH">/opt/conda</env>
                        <env name="NETCDF_FORTRAN_PATH">/opt/conda</env>
                </environment_variables>
        </machine>
        ...
  </config_machines>

XML Elements
````````````

General
:::::::

.. note::

  There are some elements; ``SAVE_TIMING_DIR``, ``SAVE_TIMING_DIR_PROJECTS``, ``TESTS`` that are model-specific and are not required.

=========================== ==================================
Element                     Description
=========================== ==================================
DESC                        A text description of the machine.
NODENAME_REGEX              A regular expression used to identify the machine.
NODE_FAIL_REGEX             A regular expression to identify node failures.
MPIRUN_RETRY_REGEX          A regular expression to identify MPI run retries.
MPIRUN_RETRY_COUNT          The number of times to retry MPI runs.
OS                          The machine's operating system.
PROXY                       Optional HTTP proxy for internet access.
COMPILERS                   Compilers supported on the machine.
MPILIBS                     MPI libraries supported on the machine. Multiple values may be defined by the compiler attribute.
PROJECT                     A project or account number used for batch jobs.
CHARGE_ACCOUNT              The charge account for the project.
SAVE_TIMING_DIR             Directory for archiving timing output.
SAVE_TIMING_DIR_PROJECTS    Projects whose jobs archive timing output.
CIME_OUTPUT_ROOT            Base directory for case output.
CIME_HTML_ROOT              Directory for HTML output.
CIME_URL_ROOT               URL root for CIME.
DIN_LOC_ROOT                Location of the input data directory.
DIN_LOC_ROOT_CLMFORC        Location for CLM forcing data.
DOUT_S_ROOT                 Root directory of short-term archive files.
BASELINE_ROOT               Root directory for system test baseline files.
CCSM_CPRNC                  Location of the cprnc tool.
PERL5LIB                    Perl library path.
GMAKE                       GNU-compatible make tool.
GMAKE_J                     Number of threads for gmake.
TESTS                       List of tests to run on the machine.
NTEST_PARALLEL_JOBS         Number of parallel jobs for testing.
BATCH_SYSTEM                Batch system used on the machine.
ALLOCATE_SPARE_NODES        Allocate spare nodes.
SUPPORTED_BY                Contact information for support.
MAX_TASKS_PER_NODE          Maximum number of tasks per node. Multiple values may be defined by the compiler attribute.
MEM_PER_TASK                Memory per task. Multiple values may be defined by the compiler attribute.
MAX_MEM_PER_NODE            Maximum memory per node. Multiple values may be defined by the compiler attribute.
MAX_GPUS_PER_NODE           Maximum GPUs per node. Multiple values may be defined by the compiler attribute.
MAX_MPITASKS_PER_NODE       Maximum MPI tasks per node. Multiple values may be defined by the compiler attribute.
MAX_CPUTASKS_PER_GPU_NODE   Maximum CPU tasks per GPU node. Multiple values may be defined by the compiler attribute.
MPI_GPU_WRAPPER_SCRIPT      MPI GPU wrapper script. Multiple values may be defined by the compiler attribute.
COSTPES_PER_NODE            Cost per node.
PROJECT_REQUIRED            Indicates if a project is required.
RUNDIR                      Directory for running the case.
EXEROOT                     Directory for executable files.
TEST_TPUT_TOLERANCE         Throughput tolerance for tests.
TEST_MEMLEAK_TOLERANCE      Memory leak tolerance for tests.
MAX_GB_OLD_TEST_DATA        Maximum GB of old test data.
=========================== ==================================

MPI
::::
There can be multiple ``mpirun`` elements. The combination of attributes makes them unique.

=================== =====================================
Element             Description
=================== =====================================
mpirun              Top-level element can contain ``compiler``, ``queue``, ``threaded``, ``unit_testing``, or ``comp_interface`` attributes.
aprun_mode          If ``executable`` contains ``aprun`` then this element's value is used to define the aprun mode.
executable          The executable to run.
arguments           Arguments to the MPI executable.
arg                 Argument to the MPI executable.
run_exe             Overrides the ``default_run_exe``.
run_misc_suffix     Overrides the ``default_run_misc_suffix``.
=================== =====================================

.. code-block:: xml
  
  <mpirun compiler="" queue="" mpilib="" threaded="" unit_testing="" comp_interface="">
        <aprun_mode></aprun_mode>
        <executable></executable>
        <arguments>
        <arg position="" name=""></arg>
        </arguments>
        <run_exe></run_exe>
        <run_misc_suffix></run_misc_suffix>
  </mpirun>

Aprun
.....
The ``<aprun_mode>`` element can be one of the following. The default value is ``ignore``.

* ``ignore`` will cause CIME to ignore its aprun module and join the values found in ``<arguments>``.
* ``default`` will use CIME's aprun module to generate arguments.
* ``override`` behaves the same as ``default`` except it will use ``<arguments>`` to mutate the generated arguments. When using this mode a ``position`` attribute can be placed on ``<arg>`` tags to specify how it's used.

The ``position`` attribute on ``<arg>`` can take one of the following values. The default value is ``per``.

* ``global`` causes the value of the ``<arg>`` element to be used as a global argument for ``aprun``.
* ``per`` causes the value of the ``<arg>`` element to be appended to each separate binary's arguments.

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

Module System
:::::::::::::
=============== ===========================================
Element         Description
=============== ===========================================
module_system   Top-level element can contain ``type`` and ``allow_error`` attributes.
init_path       Path to the module system initialization.
cmd_path        Path to the module system commands.
modules         Can have multiple where the combination of ``compiler``, ``DEBUG``, ``PIO_VERSION``, ``mpilib``, ``comp_interface``, and ``gpu_type`` make them unique.
command         Command to run where ``name`` is the action e.g. load, switch, unload and the value is the module to use e.g. netcdf-parallel/3.4
=============== ===========================================

.. code-block:: xml

  <module_system type="" allow_error="">
        <init_path lang="">
        </init_path>
        <cmd_path lang="">
        </cmd_path>
        <modules compiler="" DEBUG="" PIO_VERSION="" mpilib="" comp_interface="" gpu_type="">
                <command name="">
                </command>
        </modules>
  </module_system>

Environment Variables
:::::::::::::::::::::
=========================== ============================================
Element                     Description
=========================== ============================================
environment_variables       Can have multiple where the ``compiler`` and ``mpilib`` attributes make them unique.
env                         Can have multiple where the combination of ``name`` makes them unique.
=========================== ============================================

.. code-block:: xml
    
  <environment_variables compiler="" mpilib="">
        <env name="" source=""></env>
  </environment_variables>

Resource Limits
:::::::::::::::
=================== =====================================================
Element             Description
=================== =====================================================
resource_limits     Can have multiple where the ``DEBUG``, ``mpilib``, ``compiler``, and ``unit_testing`` make them unique.
resource            Defines the resource name and value. Can have multiples where name makes them unique.
=================== =====================================================
  
.. code-block:: xml

  <resource_limits DEBUG="" mpilib="" compiler="" unit_testing="">
        <resource name=""></resource>
  </resource_limits>

Schema
------

Version 3.0
````````````

.. code-block:: xml

    <!-- Generated with generate_xmlschema.py ../CIME/data/config/xml_schemas/config_machines_version3.xsd config_machines on 2025-03-01 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurrences min: 1 max: 1-->
    <config_machines version="">
            <!-- Occurrences min: 0 max: 1-->
            <NODENAME_REGEX>
                    <!-- Attributes 'None' is None-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <value None=""></value>
            </NODENAME_REGEX>
            <!-- Attributes 'MACH' is required-->
            <!-- Occurrences min: 0 max: Unlimited-->
            <machine MACH="">
                    <!-- Occurrences min: 1 max: 1-->
                    <DESC></DESC>
                    <!-- Occurrences min: 0 max: 1-->
                    <NODE_FAIL_REGEX></NODE_FAIL_REGEX>
                    <!-- Occurrences min: 0 max: 1-->
                    <MPIRUN_RETRY_REGEX></MPIRUN_RETRY_REGEX>
                    <!-- Occurrences min: 0 max: 1-->
                    <MPIRUN_RETRY_COUNT></MPIRUN_RETRY_COUNT>
                    <!-- Occurrences min: 1 max: 1-->
                    <OS></OS>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROXY></PROXY>
                    <!-- Occurrences min: 1 max: 1-->
                    <COMPILERS></COMPILERS>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MPILIBS compiler=""></MPILIBS>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROJECT></PROJECT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CHARGE_ACCOUNT></CHARGE_ACCOUNT>
                    <!-- Occurrences min: 0 max: 1-->
                    <SAVE_TIMING_DIR></SAVE_TIMING_DIR>
                    <!-- Occurrences min: 0 max: 1-->
                    <SAVE_TIMING_DIR_PROJECTS></SAVE_TIMING_DIR_PROJECTS>
                    <!-- Occurrences min: 1 max: 1-->
                    <CIME_OUTPUT_ROOT></CIME_OUTPUT_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CIME_HTML_ROOT></CIME_HTML_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CIME_URL_ROOT></CIME_URL_ROOT>
                    <!-- Occurrences min: 1 max: 1-->
                    <DIN_LOC_ROOT></DIN_LOC_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <DIN_LOC_ROOT_CLMFORC></DIN_LOC_ROOT_CLMFORC>
                    <!-- Occurrences min: 1 max: 1-->
                    <DOUT_S_ROOT></DOUT_S_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <BASELINE_ROOT></BASELINE_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CCSM_CPRNC></CCSM_CPRNC>
                    <!-- Occurrences min: 0 max: 1-->
                    <PERL5LIB></PERL5LIB>
                    <!-- Occurrences min: 0 max: 1-->
                    <GMAKE></GMAKE>
                    <!-- Occurrences min: 0 max: 1-->
                    <GMAKE_J></GMAKE_J>
                    <!-- Occurrences min: 0 max: 1-->
                    <TESTS></TESTS>
                    <!-- Occurrences min: 0 max: 1-->
                    <NTEST_PARALLEL_JOBS></NTEST_PARALLEL_JOBS>
                    <!-- Occurrences min: 1 max: 1-->
                    <BATCH_SYSTEM></BATCH_SYSTEM>
                    <!-- Occurrences min: 0 max: 1-->
                    <ALLOCATE_SPARE_NODES></ALLOCATE_SPARE_NODES>
                    <!-- Occurrences min: 1 max: 1-->
                    <SUPPORTED_BY></SUPPORTED_BY>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MAX_TASKS_PER_NODE compiler=""></MAX_TASKS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MEM_PER_TASK compiler=""></MEM_PER_TASK>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_MEM_PER_NODE compiler=""></MAX_MEM_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_GPUS_PER_NODE compiler=""></MAX_GPUS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MAX_MPITASKS_PER_NODE compiler=""></MAX_MPITASKS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <MAX_CPUTASKS_PER_GPU_NODE compiler=""></MAX_CPUTASKS_PER_GPU_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MPI_GPU_WRAPPER_SCRIPT compiler=""></MPI_GPU_WRAPPER_SCRIPT>
                    <!-- Occurrences min: 0 max: 1-->
                    <COSTPES_PER_NODE></COSTPES_PER_NODE>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROJECT_REQUIRED></PROJECT_REQUIRED>
                    <!-- Attributes 'compiler' is optional,'queue' is optional,'mpilib' is optional,'threaded' is optional,'unit_testing' is optional,'comp_interface' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <mpirun compiler="" queue="" mpilib="" threaded="" unit_testing="" comp_interface="">
                            <!-- Occurrences min: 0 max: 1-->
                            <aprun_mode></aprun_mode>
                            <!-- Occurrences min: 1 max: 1-->
                            <executable></executable>
                            <!-- Occurrences min: 0 max: 1-->
                            <arguments>
                                    <!-- Attributes 'None' is None-->
                                    <!-- Occurrences min: 0 max: Unlimited-->
                                    <arg None="">
                                        <!-- Occurrences min: 0 max: Unlimited-->
                                    </arg>
                            </arguments>
                            <!-- Occurrences min: 0 max: 1-->
                            <run_exe></run_exe>
                            <!-- Occurrences min: 0 max: 1-->
                            <run_misc_suffix></run_misc_suffix>
                    </mpirun>
                    <!-- Attributes 'type' is required,'allow_error' is optional-->
                    <!-- Occurrences min: 1 max: 1-->
                    <module_system type="" allow_error="">
                            <!-- Attributes 'lang' is required-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <init_path lang="">
                            </init_path>
                            <!-- Attributes 'lang' is required-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <cmd_path lang="">
                            </cmd_path>
                            <!-- Attributes 'compiler' is optional,'DEBUG' is optional,'PIO_VERSION' is optional,'mpilib' is optional,'comp_interface' is optional,'gpu_type' is optional-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <modules compiler="" DEBUG="" PIO_VERSION="" mpilib="" comp_interface="" gpu_type="">
                                    <!-- Attributes 'name' is required-->
                                    <!-- Occurrences min: 1 max: Unlimited-->
                                    <command name="">
                                    </command>
                            </modules>
                    </module_system>
                    <!-- Occurrences min: 0 max: 1-->
                    <RUNDIR></RUNDIR>
                    <!-- Occurrences min: 0 max: 1-->
                    <EXEROOT></EXEROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <TEST_TPUT_TOLERANCE></TEST_TPUT_TOLERANCE>
                    <!-- Occurrences min: 0 max: 1-->
                    <TEST_MEMLEAK_TOLERANCE></TEST_MEMLEAK_TOLERANCE>
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_GB_OLD_TEST_DATA></MAX_GB_OLD_TEST_DATA>
                    <!-- Attributes 'None' is None-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <environment_variables None="">
                            <!-- Attributes 'name' is optional,'source' is optional-->
                            <!-- Occurrences min: 1 max: Unlimited-->
                            <env name="" source="">
                            </env>
                    </environment_variables>
                    <!-- Attributes 'DEBUG' is optional,'mpilib' is optional,'compiler' is optional,'unit_testing' is optional-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <resource_limits DEBUG="" mpilib="" compiler="" unit_testing="">
                            <!-- Attributes 'name' is required-->
                            <!-- Occurrences min: 1 max: Unlimited-->
                            <resource name="">
                            </resource>
                    </resource_limits>
            </machine>
            <!-- Occurrences min: 0 max: 1-->
            <default_run_suffix>
                    <!-- Occurrences min: 1 max: 1-->
                    <default_run_exe></default_run_exe>
                    <!-- Occurrences min: 1 max: 1-->
                    <default_run_misc_suffix></default_run_misc_suffix>
            </default_run_suffix>
    </config_machines>

Version 2.0
```````````
.. code-block:: xml

    <!-- Generated with generate_xmlschema.py ../CIME/data/config/xml_schemas/config_machines.xsd config_machines on 2025-03-01 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurrences min: 1 max: 1-->
    <config_machines version="">
            <!-- Attributes 'MACH' is required-->
            <!-- Occurrences min: 1 max: Unlimited-->
            <machine MACH="">
                    <!-- Occurrences min: 1 max: 1-->
                    <DESC></DESC>
                    <!-- Occurrences min: 0 max: 1-->
                    <NODENAME_REGEX></NODENAME_REGEX>
                    <!-- Occurrences min: 0 max: 1-->
                    <NODE_FAIL_REGEX></NODE_FAIL_REGEX>
                    <!-- Occurrences min: 0 max: 1-->
                    <MPIRUN_RETRY_REGEX></MPIRUN_RETRY_REGEX>
                    <!-- Occurrences min: 0 max: 1-->
                    <MPIRUN_RETRY_COUNT></MPIRUN_RETRY_COUNT>
                    <!-- Occurrences min: 1 max: 1-->
                    <OS></OS>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROXY></PROXY>
                    <!-- Occurrences min: 1 max: 1-->
                    <COMPILERS></COMPILERS>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MPILIBS compiler=""></MPILIBS>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROJECT></PROJECT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CHARGE_ACCOUNT></CHARGE_ACCOUNT>
                    <!-- Occurrences min: 0 max: 1-->
                    <SAVE_TIMING_DIR></SAVE_TIMING_DIR>
                    <!-- Occurrences min: 0 max: 1-->
                    <SAVE_TIMING_DIR_PROJECTS></SAVE_TIMING_DIR_PROJECTS>
                    <!-- Occurrences min: 1 max: 1-->
                    <CIME_OUTPUT_ROOT></CIME_OUTPUT_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CIME_HTML_ROOT></CIME_HTML_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CIME_URL_ROOT></CIME_URL_ROOT>
                    <!-- Occurrences min: 1 max: 1-->
                    <DIN_LOC_ROOT></DIN_LOC_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <DIN_LOC_ROOT_CLMFORC></DIN_LOC_ROOT_CLMFORC>
                    <!-- Occurrences min: 1 max: 1-->
                    <DOUT_S_ROOT></DOUT_S_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <BASELINE_ROOT></BASELINE_ROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <CCSM_CPRNC></CCSM_CPRNC>
                    <!-- Occurrences min: 0 max: 1-->
                    <PERL5LIB></PERL5LIB>
                    <!-- Occurrences min: 0 max: 1-->
                    <GMAKE></GMAKE>
                    <!-- Occurrences min: 0 max: 1-->
                    <GMAKE_J></GMAKE_J>
                    <!-- Occurrences min: 0 max: 1-->
                    <TESTS></TESTS>
                    <!-- Occurrences min: 0 max: 1-->
                    <NTEST_PARALLEL_JOBS></NTEST_PARALLEL_JOBS>
                    <!-- Occurrences min: 1 max: 1-->
                    <BATCH_SYSTEM></BATCH_SYSTEM>
                    <!-- Occurrences min: 0 max: 1-->
                    <ALLOCATE_SPARE_NODES></ALLOCATE_SPARE_NODES>
                    <!-- Occurrences min: 1 max: 1-->
                    <SUPPORTED_BY></SUPPORTED_BY>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MAX_TASKS_PER_NODE compiler=""></MAX_TASKS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MEM_PER_TASK compiler=""></MEM_PER_TASK>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_MEM_PER_NODE compiler=""></MAX_MEM_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_GPUS_PER_NODE compiler=""></MAX_GPUS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <MAX_MPITASKS_PER_NODE compiler=""></MAX_MPITASKS_PER_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <MAX_CPUTASKS_PER_GPU_NODE compiler=""></MAX_CPUTASKS_PER_GPU_NODE>
                    <!-- Attributes 'compiler' is optional-->
                    <!-- Occurrences min: 0 max: 1-->
                    <MPI_GPU_WRAPPER_SCRIPT compiler=""></MPI_GPU_WRAPPER_SCRIPT>
                    <!-- Occurrences min: 0 max: 1-->
                    <COSTPES_PER_NODE></COSTPES_PER_NODE>
                    <!-- Occurrences min: 0 max: 1-->
                    <PROJECT_REQUIRED></PROJECT_REQUIRED>
                    <!-- Attributes 'compiler' is optional,'queue' is optional,'mpilib' is optional,'threaded' is optional,'unit_testing' is optional,'comp_interface' is optional-->
                    <!-- Occurrences min: 1 max: Unlimited-->
                    <mpirun compiler="" queue="" mpilib="" threaded="" unit_testing="" comp_interface="">
                            <!-- Occurrences min: 0 max: 1-->
                            <aprun_mode></aprun_mode>
                            <!-- Occurrences min: 1 max: 1-->
                            <executable></executable>
                            <!-- Occurrences min: 0 max: 1-->
                            <arguments>
                                    <!-- Attributes 'None' is None-->
                                    <!-- Occurrences min: 0 max: Unlimited-->
                                    <arg None="">
                                        <!-- Occurrences min: 0 max: Unlimited-->
                                    </arg>
                            </arguments>
                            <!-- Occurrences min: 0 max: 1-->
                            <run_exe></run_exe>
                            <!-- Occurrences min: 0 max: 1-->
                            <run_misc_suffix></run_misc_suffix>
                    </mpirun>
                    <!-- Attributes 'type' is required,'allow_error' is optional-->
                    <!-- Occurrences min: 1 max: 1-->
                    <module_system type="" allow_error="">
                            <!-- Attributes 'lang' is required-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <init_path lang="">
                            </init_path>
                            <!-- Attributes 'lang' is required-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <cmd_path lang="">
                            </cmd_path>
                            <!-- Attributes 'compiler' is optional,'DEBUG' is optional,'PIO_VERSION' is optional,'mpilib' is optional,'comp_interface' is optional,'gpu_type' is optional-->
                            <!-- Occurrences min: 0 max: Unlimited-->
                            <modules compiler="" DEBUG="" PIO_VERSION="" mpilib="" comp_interface="" gpu_type="">
                                    <!-- Attributes 'name' is required-->
                                    <!-- Occurrences min: 1 max: Unlimited-->
                                    <command name="">
                                    </command>
                            </modules>
                    </module_system>
                    <!-- Occurrences min: 0 max: 1-->
                    <RUNDIR></RUNDIR>
                    <!-- Occurrences min: 0 max: 1-->
                    <EXEROOT></EXEROOT>
                    <!-- Occurrences min: 0 max: 1-->
                    <TEST_TPUT_TOLERANCE></TEST_TPUT_TOLERANCE>
                    <!-- Occurrences min: 0 max: 1-->
                    <TEST_MEMLEAK_TOLERANCE></TEST_MEMLEAK_TOLERANCE>
                    <!-- Occurrences min: 0 max: 1-->
                    <MAX_GB_OLD_TEST_DATA></MAX_GB_OLD_TEST_DATA>
                    <!-- Attributes 'None' is None-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <environment_variables None="">
                            <!-- Attributes 'name' is optional,'source' is optional-->
                            <!-- Occurrences min: 1 max: Unlimited-->
                            <env name="" source="">
                            </env>
                    </environment_variables>
                    <!-- Attributes 'DEBUG' is optional,'mpilib' is optional,'compiler' is optional,'unit_testing' is optional-->
                    <!-- Occurrences min: 0 max: Unlimited-->
                    <resource_limits DEBUG="" mpilib="" compiler="" unit_testing="">
                            <!-- Attributes 'name' is required-->
                            <!-- Occurrences min: 1 max: Unlimited-->
                            <resource name="">
                            </resource>
                    </resource_limits>
            </machine>
            <!-- Occurrences min: 0 max: 1-->
            <default_run_suffix>
                <!-- Occurrences min: 1 max: 1-->
                <default_run_exe></default_run_exe>
                <!-- Occurrences min: 1 max: 1-->
                <default_run_misc_suffix></default_run_misc_suffix>
            </default_run_suffix>
    </config_machines>