.. _system_tests:

System Testing
==============

.. contents::
    :local:

Overview
--------
The ``create_test``` tool is a versatile and powerful utility provided by CIME for automating the creation, setup, building, and execution of system tests. It simplifies the process of running tests by allowing users to specify test configurations through a single command. The tool supports a wide range of test types, modifiers, and options, making it highly customizable to meet various testing needs.

Key features of ``create_test`` include:

* Automated creation and setup of test cases.
* Building and running tests with specified configurations.
* Support for multiple test types and modifiers.
* Ability to run individual tests or suites of tests.
* Integration with baseline comparison and performance testing.
* Detailed logging and status reporting for each phase of the test.

The ``create_test`` tool is essential for ensuring the reliability and correctness of the model by providing a streamlined and efficient way to conduct comprehensive system tests.

Testing a Case
--------------
To run a system test(s) CIME provides ``create_test``. This tool provides much of the same functionality as ``create_newcase`` allowing to define a non-default compiler, queue, override the output location of the test cases, etc.

CIME has functionality to create baselines fors tests, and compare future runs to track changes in answers.

The tool supports running single, or multiple tests. Multiple tests can be defined by just their test names on the CLI or by providing an XML or Python file.

.. _system_testing-individual:

Run a individual tests
``````````````````````
The following will run a single test case.

.. code-block:: bash

  ./scripts/create_test <testname>

The following will run multiple test cases.

.. code-block:: bash

  ./scripts/create_test <testname> <testname> 

These test names could also be placed a file and run with the follow command.

.. code-block:: bash

  ./scripts/create_test -f <filename>

Run a test suite
````````````````
The following will run an entire test suite of test cases.

.. code-block:: bash

  ./scripts/create_test <testsuite>

XML
:::
A pre-defined suite of test can be run by passing the ``--xml`` argument to ``create_test``.

This argument will cause CIME to load ``testlist*.xml`` files. As described in https://github.com/ESCOMP/ctsm/wiki/System-Testing-Guide, to determine what pre-defined test suites are available and what tests they contain, you can run ``./scripts/query_testlists``.

Test suites are retrieved in create_test via 3 selection attributes::

    --xml-category your_category   The test category.
    --xml-machine  your_machine    The machine.
    --xml-compiler your_compiler   The compiler.

| If none of these 3 are used, the default values are 'none'.
| If any of them are used, the default for the unused options is 'all'.
| Existing values of these attributes can be seen by running ``query_testlists``

The search for test names can be restricted to a single test list using::

    --xml-testlist your_testlist

Omitting this results in searching all testlists listed in::

    cime/config/{cesm,e3sm}/config_files.xml

The ``./scripts/query_testlists`` tool gathers descriptions of the tests and testlists available
in the XML format, the components, and projects.

The ``--xml-{compiler,machine,category,testlist}`` arguments can be used
as in create_test (above) to focus the search.
The 'category' descriptor of a test can be used to run a group of associated tests at the same time.
The available categories, with the tests they encompass, can be listed by::

   ./query_testlists --define-testtypes

The ``--show-options`` argument does the same, but displays the 'options' defined for the tests,
such as queue, walltime, etc.

Adding a test requires first deciding which compset will be tested
and then finding the appropriate ``testlist_$component.xml`` file::

    components/$component/cime_config/testdefs/
       testlist_$component.xml
       testmods_dirs/$component/{TESTMODS1,TESTMODS2,...}
    cime_config/
       testlist_allactive.xml
       testmods_dirs/allactive/{defaultio,...}

You can optionally add testmods for that test in the testmods_dirs.
Testlists and testmods live in different paths for cime, drv, and components.

If this test will only be run as a single test, you can now create a test name
and follow the `individual <system_testing-individual_>`_ test instructions for create_test.

Python
::::::
A suite of tests can also be provided with a python file ``tests.py`` placed in ``$MODEL/cime_config``.

To run a test suite called e3sm_developer::

  ./create_test e3sm_developer

One can exclude a specific test from a suite::

  ./create_test e3sm_developer ^SMS.f19_f19.A

See ``./scripts/create_test -h`` for the full list of options.

Format
......
The following defines the format of ``tests.py``. The only variable that needs to be defined is ``_TESTS`` which needs to be a dictionary. Each key is the name of a test suite and the value is a dictionary. See below for the description of possible values.

========== ==================================================================
Key         Description
========== ==================================================================
inherit     A tuple, list, or str of other suites.
time        Upper limit for test time. Format is ``HH:MM:SS``.
share       Should cases share a build. Value is ``true`` or ``false``.
tests       A tuple, list, or str of ``<testname>``, see the format below.
========== ==================================================================

The format for ``<testname>`` is ``TESTTYPE.GRID.COMPSET[.TESTMOD]``. The ``TESTMOD`` is optional.

Example
.......

.. code-block:: python

  _TESTS = {
    "suite_a": {
      "inherit": ("suite_b"),
      "time": "0:45:00",
      "share": "true",
      "tests": (
        <testname>
      )
    },
    "suite_b": {
      "time": "02:00:00",
      "tests": (
        <testname>
      )
    }
  }

Listing the test suites
.......................
The following tool will list the tests.::

  ./CIME/Tools/list_e3sm_tests -t compsets e3sm_developer

Will list all the compsets tested in the ``e3sm_developer`` test suite.

Test name syntax
----------------
A test name is defined by the following format, where anything enclosed in ``[]`` is option.

.. code-block::
  
  TESTTYPE[_MODIFIERS].GRID.COMPSET[.MACHINE_COMPILER][.GROUP-TESTMODS]

The following is a minimal example where ``ERP`` is the ``TESTTYPE``, ``ne4pg2_oQU480`` is the ``GRID`` and ``F2010`` is the ``COMPSET``.

.. code-block::

  ERP.ne4pg2_oQU480.F2010


Below is a breakdown of the different parts of the ``testname`` syntax.

=================  =====================================================================================
Syntax Part        Description
=================  =====================================================================================
TESTTYPE           The type of test e.g. SMS, ERS, etc. See ``config_tests.xml`` for options.
MODIFIER           Changes to the default settings for the test type.
GRID               The model grid, can be longname or alias.
COMPSET            The compset, can be a longname but usually a compset alias.
MACHINE            This is optional; if this value is not supplied, ``create_test`` will probe the underlying machine.
COMPILER           If this value is not supplied, use the default compiler for MACHINE.
GROUP-TESTMODS     This is optional. This points to a directory with testmod.
=================  =====================================================================================

Test Type
``````````
The test type defines the behavior that the case will be tested against. For example a test may exercise a models ability to restart, invariance with MPI task count, or short term archiving.

CIME provides some tests out of the box, but a model may add additional test types using the ``SYSTEM_TEST_DIR`` variable or adding them to ``cime_config/SystemTests`` in any component.

The following test types are provided by CIME.

.. _system-testings-types:

============ =====================================================================================
TESTTYPE     Description
============ =====================================================================================
   ERS       Exact restart from startup (default 6 days + 5 days)
              | Do an 11-day initial test - write a restart at day 6.    (file suffix: base)
              | Do a 5-day restart test, starting from restart at day 6. (file suffix: rest)
              | Compare component history files '.base' and '.rest' at day 11 with cprnc
              |    PASS if they are identical.

   ERT       Longer version of ERS. Exact restart from startup, default 2 months + 1 month (ERS with info DBUG = 1).

   IRT       Exact restart from startup, (default 4 days + 7 days) with restart from interim file.

   ERIO      Exact restart from startup with different IO file types, (default 6 days + 5 days).

   ERR       Exact restart from startup with resubmit, (default 4 days + 3 days).

   ERRI      Exact restart from startup with resubmit, (default 4 days + 3 days). Tests incomplete logs option for st_archive.

   ERI       Hybrid/branch/exact restart test, default (by default STOP_N is 22 days)
              ref1case
                Do an initial run for 3 days writing restarts at day 3.
                ref1case is a clone of the main case.
                Short term archiving is on.
              ref2case (Suffix hybrid)
                Do a hybrid run for default 19 days running with ref1 restarts from day 3,
                and writing restarts at day 10.
                ref2case is a clone of the main case.
                Short term archiving is on.
              case
                Do a branch run, starting from restarts written in ref2case,
                for 9 days and writing restarts at day 5.
                Short term archiving is off.
              case (Suffix base)
                Do a restart run from the branch run restarts for 4 days.
                Compare component history files '.base' and '.hybrid' at day 19.
                Short term archiving is off.

   ERP       PES counts hybrid (OPENMP/MPI) restart bit-for-bit test from startup, (default 6 days + 5 days).
              Initial PES set up out of the box
              Do an 11-day initial test - write a restart at day 6.     (file suffix base)
              Half the number of tasks and threads for each component.
              Do a 5-day restart test starting from restart at day 6. (file suffix rest)
              Compare component history files '.base' and '.rest' at day 11.
              This is just like an ERS test but the tasks/threading counts are modified on restart.

   PEA       Single PE bit-for-bit test (default 5 days)
              Do an initial run on 1 PE with mpi library.     (file suffix: base)
              Do the same run on 1 PE with mpiserial library. (file suffix: mpiserial)
              Compare base and mpiserial.

   PEM       Modified PE counts for MPI(NTASKS) bit-for-bit test (default 5 days)
              Do an initial run with default PE layout                                     (file suffix: base)
              Do another initial run with modified PE layout (NTASKS_XXX => NTASKS_XXX/2)  (file suffix: modpes)
              Compare base and modpes.

   PET       Modified threading OPENMP bit-for-bit test (default 5 days)
              Do an initial run where all components are threaded by default. (file suffix: base)
              Do another initial run with NTHRDS=1 for all components.        (file suffix: single_thread)
              Compare base and single_thread.

   PFS       Performance test setup. History and restart output is turned off. (default 20 days)

   ICP       CICE performance test.

   OCP       POP performance test. (default 10 days)

   MCC       Multi-driver validation vs single-driver (both multi-instance). (default 5 days)

   NCK       Multi-instance validation vs single instance - sequential PE for instances (default length)
              Do an initial run test with NINST 1. (file suffix: base)
              Do an initial run test with NINST 2. (file suffix: multiinst for both _0001 and _0002)
              Compare base and _0001 and _0002.

   REP       Reproducibility: Two identical initial runs are bit-for-bit. (default 5 days)

   SBN       Smoke build-namelist test (just run preview_namelist and check_input_data).

   SMS       Smoke test (default 5 days)
              Do a 5-day initial test that runs to completion without error. (file suffix: base)

   SEQ       Different sequencing bit-for-bit test. (default 10 days)
              Do an initial run test with out-of-box PE-layout. (file suffix: base)
              Do a second run where all root pes are at pe-0.   (file suffix: seq)
              Compare base and seq.

   DAE       Data assimilation test, default 1 day, two DA cycles, no data modification.

   PRE       Pause-resume test: by default a bit-for-bit test of pause-resume cycling.
              Default 5 hours, five pause/resume cycles, no data modification.
============ =====================================================================================

The tests run for a default length indicated above, will use default pelayouts for the case
on the machine the test runs on and its default coupler and MPI library. It is possible to modify
elements of the test through a test type modifier.

Modifiers
`````````

============ =====================================================================================
MODIFIERS    Description
============ =====================================================================================
   _C#       Set number of instances to # and use the multi driver (can't use with _N).

   _cG       CALENDAR set to "GREGORIAN".

   _D        XML variable DEBUG set to "TRUE".

   _I        Marker to distinguish tests with the same name - ignored.

   _Lo#      Run length set by o (STOP_OPTION) and # (STOP_N).
              | o = {"y":"nyears", "m":"nmonths",  "d":"ndays",
              |     \ "h":"nhours", "s":"nseconds", "n":"nsteps"}

   _Mx       Set MPI library to x.

   _N#       Set number of instances to # and use a single driver (can't use with _C).

   _Px       Set create_newcase's ``--pecount`` to x, which is usually N (tasks) or NxM (tasks x threads per task).

   _R        For testing in PTS_MODE or Single Column Model (SCM) mode.
             For PTS_MODE, compile with mpi-serial.

   _Vx       Set driver to x.
              |

============ =====================================================================================

For example, this will run the ERP test with debugging turned on during compilation::

    ./scripts/create_test ERP_D.ne4pg2_oQU480.F2010

This will run the ERP test for 3 days instead of the default 11 days::

    ./scripts/create_test ERP_Ld3.ne4pg2_oQU480.F2010

You can combine test type modifiers::

    ./scripts/create_test ERP_D_Ld3.ne4pg2_oQU480.F2010

Test Mods
```````````````
The ``create_test`` tool works with out-of-the-box compsets and grids.
Sometimes you may want to run a test with modifications to a namelist or other setting without creating an entire compset. CIME provides the testmods capability for this situation.

The ``GROUP-TESTMODS`` string is at the end of the full testname (including machine and compiler).

The syntax for ``GROUP-TESTMODS`` is as follows.

============ =====================================================================================
Syntax part  Description
============ =====================================================================================
GROUP        Name of the directory relative to ``TESTS_MODS_DIR`` that contains ``TESTMODS``.

TESTMODS     Name of the directory under ``GROUP`` that contains any combination of `user_nl_*`, `shell_commands`, `user_mods`, or `params.py`.
============ =====================================================================================

.. note::

  A test mod can contain any combination of ``user_nl_*``, ``shell_commands``, ``user_mods``, or ``params.py``.

For example, the ``ERP`` test for an E3SM ``F-case`` can be modified to use a different radiation scheme by using ``eam-rrtmgp``::

  ERP_D_Ld3.ne4pg2_oQU480.F2010.pm-cpu_intel.eam-rrtmgp

If ``TESTS_MODS_DIR`` was set to ``$E3SM/components/eam/cime_config/testdefs/testmods_dirs`` then the
directory containing the testmods would be ``$E3SM/components/eam/cime_config/testdefs/testmods_dirs/eam/rrtmpg``.

In this directory, you'd find a `shell_commands`` file containing the following::

  #!/bin/bash
  ./xmlchange --append CAM_CONFIG_OPTS='-rad rrtmgp'

These commands are applied after the testcase is created and case.setup is called.

.. warning::
  
  Do not use '-' in the testmods directory name because it has a special meaning to ``create_test``.

Testing Process
------------------------

Each test run by ``create_test`` includes the following mandatory steps:

================= =====================================================================================
Phase             Description
================= =====================================================================================
CREATE_NEWCASE    Creates the case directory (case.create_newcase)
XML               XML changes to case based on test settings (xmlchange)
SETUP             Setup case (case.setup)
SHAREDLIB_BUILD   Build sharedlibs (case.build)
MODEL_BUILD       Build model (case.build)
SUBMIT            Submit test (case.submit)
RUN               Run test
================= =====================================================================================

And the following optional phases:

================= =====================================================================================
Phase             Description
================= =====================================================================================
NLCOMP            Compare namelists against baseline
THROUGHPUT        Compare throughput against baseline
MEMCOMP           Compare memory usage against baseline
MEMLEAK           Check for memory leaks
COMPARE           Used to track test-specific comparisons, for example, an ERS test would have a COMPARE_base_rest phase representing the check that the base result matched the restart result.
GENERATE          Generate baseline results
BASELINE          Compare results against baselines
================= =====================================================================================

Each phase within the test may be in one of the following states:

================= =====================================================================================
State             Description
================= ===================================================================================== 
PASS              The phase was executed successfully
FAIL              We attempted to execute this phase, but it failed. If this phase is mandatory, no further progress will be made on this test. A detailed explanation of the failure should be in TestStatus.log.
PEND              This phase will be run or is currently running but not complete
================= =====================================================================================

Output
```````
Lets look at the output from ``./scripts/create_test SMS.f19_f19.A``. Here you can find each phase of the test its status and the time it took to complete.

.. code-block:: bash

  Creating test directory /home/jgfouca/e3sm/scratch/SMS.f19_f19.A.melvin_gnu.20170504_163152_31aahy
  RUNNING TESTS:
    SMS.f19_f19.A.melvin_gnu
  Starting CREATE_NEWCASE for test SMS.f19_f19.A.melvin_gnu with 1 procs
  Finished CREATE_NEWCASE for test SMS.f19_f19.A.melvin_gnu in 4.170537 seconds (PASS)
  Starting XML for test SMS.f19_f19.A.melvin_gnu with 1 procs
  Finished XML for test SMS.f19_f19.A.melvin_gnu in 0.735993 seconds (PASS)
  Starting SETUP for test SMS.f19_f19.A.melvin_gnu with 1 procs
  Finished SETUP for test SMS.f19_f19.A.melvin_gnu in 11.544286 seconds (PASS)
  Starting SHAREDLIB_BUILD for test SMS.f19_f19.A.melvin_gnu with 1 procs
  Finished SHAREDLIB_BUILD for test SMS.f19_f19.A.melvin_gnu in 82.670667 seconds (PASS)
  Starting MODEL_BUILD for test SMS.f19_f19.A.melvin_gnu with 4 procs
  Finished MODEL_BUILD for test SMS.f19_f19.A.melvin_gnu in 18.613263 seconds (PASS)
  Starting RUN for test SMS.f19_f19.A.melvin_gnu with 64 procs
  Finished RUN for test SMS.f19_f19.A.melvin_gnu in 35.068546 seconds (PASS). [COMPLETED 1 of 1]
  At test-scheduler close, state is:
  PASS SMS.f19_f19.A.melvin_gnu RUN
    Case dir: /home/jgfouca/e3sm/scratch/SMS.f19_f19.A.melvin_gnu.20170504_163152_31aahy
  test-scheduler took 154.780044079 seconds

The case is created in ``$CASEDIR`` which can be seen in the output above. The test status is stored in ``$CASEDIR/TestStatus``.
The case directory name format is ``<testname>.<test-id>`` where ``<test-id>`` defaults to ``YYYYMMDD_HHMMSS_hash``.
This can be overridden with the ``--test-id`` argument to ``create_test``.

The current state of a test is represented in the file ``$CASEDIR/TestStatus``. Example output::

     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel CREATE_NEWCASE
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel XML
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel SETUP
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel SHAREDLIB_BUILD time=277
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel MODEL_BUILD time=572
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel SUBMIT
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel RUN time=208
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel COMPARE_base_rest
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel MEMLEAK insufficient data for memleak test
     PASS ERP_D_Ld3.ne4pg2_oQU480.F2010.chrysalis_intel SHORT_TERM_ARCHIVER

The entire stdout output from the test will be put in the file ``$CASEDIR/TestStatus.log``.

A ``cs.status.<test-id>`` script will also be put in the test root. This script will allow you to see the status of the test.

Baselines
---------
An important part of testing is creating, comparing, and managing baselines (sometimes called gold results). Baselines can be used to compare history files, namelist files, and performance metrics.

The ``create_test`` tool can be asked to perform bit-for-bit comparisons between the files generated by the current run and the files stored in the baseline. They must be bit-for-bit identical for the baseline test to pass.

Baseline testing adds an additional test criteria to the one that comes from the test type and is used as a way to guard against unintentionally changing the results from a deterministic climate model.

Creating a baseline
```````````````````
A baseline can be generated by passing ``-g`` to ``create_test``. There
are additional options to control generating baselines.::

  ./scripts/create_test -b master -g SMS.ne30_f19_g16_rx1.A

Comparing a baseline
`````````````````````
Comparing the output of a test to a baseline is achieved by passing ``-c`` to ``create_test``.::

  ./scripts/create_test -b master -c SMS.ne30_f19_g16_rx1.A

Suppose you accidentally changed something in the source code that does not cause the model to crash but
does cause it to change the answers it produces. In this case, the SMS test would pass (it still runs) but the
comparison with baselines would FAIL (answers are not bit-for-bit identical to the baseline) and so the test
as a whole would FAIL.

Managing baselines
```````````````````
If you intended to change the answers, you need to update the baseline with new files. This is referred to as "blessing" the test.
This is done with the ``./CIME/Tools/bless_test_results`` tool. The tool provides the ability to bless different features of the baseline. The currently supported features are namelist files, history files, and performance metrics. The performance metrics are separated into throughput and memory usage.

The following command can be used to compare a test to a baseline and bless an update to the history file.::

  ./CIME/Tools/bless_test_results -b master --hist-only SMS.ne30_f19_g16_rx1.A

The ``./CIME/Tools/compare_test_results`` tool can be used to quickly compare tests to baselines and report any ``diffs``.::

  ./CIME/Tools/compare_test_results -b master SMS.ne30_f19_g16_rx1.A

Performance baselines
`````````````````````
By default performance baselines are generated by parsing the coupler log and comparing the throughput in SYPD (Simulated Years Per Day) and the memory usage high water.

This can be customized by creating a python module under ``$MODEL/cime_config/customize``. There are four hooks that can be used to customize the generation and comparison.

- perf_get_throughput
- perf_get_memory
- perf_compare_throughput_baseline
- perf_compare_memory_baseline

.. TODO:: need to add api docs and link

The following pseudo code is an example of this customization.

.. code-block:: python

  # $DRIVER/cime_config/customize/perf_baseline.py

  def perf_get_throughput(case):
    """
    Parameters
    ----------
    case : CIME.case.case.Case
      Current case object.

    Returns
    -------
    str
      Storing throughput value.
    str
      Open baseline file for writing.
    """
    current = analyze_throughput(...)

    return json.dumps(current), "w"

  def perf_get_memory(case):
    """
    Parameters
    ----------
    case : CIME.case.case.Case
      Current case object.

    Returns
    -------
    str
      Storing memory value.
    str
      Open baseline file for writing.
    """
    current = analyze_memory(case)

    return json.dumps(current), "w"

  def perf_compare_throughput_baseline(case, baseline, tolerance):
    """
    Parameters
    ----------
    case : CIME.case.case.Case
      Current case object.
    baseline : str
      Baseline throughput value.
    tolerance : float
      Allowed difference tolerance.

    Returns
    -------
    bool
      Whether throughput diff is below tolerance.
    str
      Comments about the results.
    """
    current = analyze_throughput(case)

    baseline = json.loads(baseline)

    diff, comments = generate_diff(...)

    return diff, comments

  def perf_compare_memory_baseline(case, baseline, tolerance):
    """
    Parameters
    ----------
    case : CIME.case.case.Case
      Current case object.
    baseline : str
      Baseline memory value.
    tolerance : float
      Allowed difference tolerance.

    Returns
    -------
    bool
      Whether memory diff is below tolerance.
    str
      Comments about the results.
    """
    current = analyze_memory(case)

    baseline = json.loads(baseline)

    diff, comments = generate_diff(...)

    return diff, comments
