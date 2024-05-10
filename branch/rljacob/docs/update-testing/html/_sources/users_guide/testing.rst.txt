.. _testing:

**************
Testing Cases
**************

`create_test <../Tools_user/create_test.html>`_
is a powerful system testing capability provided by the CIME Case Control System.
create_test can, in one command, create a case, setup, build and run the case
according to the test type and return a PASS or FAIL for the test result.

.. _individual:

An individual test can be run as::

  $CIMEROOT/scripts/create_test $test_name

Everything the test will do is controlled by parsing the test name.

=================
Testname syntax
=================
.. _`Test naming`:

Tests must be named with the following forms, [ ]=optional::

  TESTTYPE[_MODIFIERS].GRID.COMPSET[.MACHINE_COMPILER][.GROUP-TESTMODS]

For example using the minimum required elements of a testname::

   $CIMEROOT/scripts/create_test ERP.ne4pg2_oQU480.F2010


=================  =====================================================================================
NAME PART
=================  =====================================================================================
TESTTYPE_          the general type of test, e.g. SMS. Options are listed in the following table and config_tests.xml.
MODIFIERS_         Changes to the default settings for the test type.
                   See the following table and test_scheduler.py.
GRID               The grid set (usually a grid alias).
COMPSET            The compset, Can be a longname but usually a compset alias
MACHINE            This is optional; if this value is not supplied, `create_test <../Tools_user/create_test.html>`_
                   will probe the underlying machine.
COMPILER           If this value is not supplied, use the default compiler for MACHINE.
GROUP-TESTMODS_    This is optional. This points to a directory with  ``user_nl_xxx`` files or a ``shell_commands``
                   that can be used to make namelist and other  modifications prior to running a test.
=================  =====================================================================================

.. _TESTTYPE:

-------------
TESTTYPE
-------------
The test types in CIME are all system tests: they compile all the code needed in a case, They test
functionality of the model such as restart capability, invariance with MPI task count, and short
term archiving. At this time, they do not test for scientific correctness.

The currently supported test types are:

============ =====================================================================================
TESTTYPE     Description
============ =====================================================================================
   ERS       Exact restart from startup (default 6 days + 5 days)
              | Do an 11 day initial test - write a restart at day 6.    (file suffix: base)
              | Do a 5 day restart test, starting from restart at day 6. (file suffix: rest)
              | Compare component history files '.base' and '.rest' at day 11 with cprnc
              |    PASS if they are identical.

   ERS2      Exact restart from startup  (default 6 days + 5 days).

              | Do an 11 day initial test without making restarts. (file suffix: base)
              | Do an 11 day restart test stopping at day 6 with a restart,
                then resuming from restart at day 6. (file suffix: rest)
              | Compare component history files ".base" and ".rest" at day 11.

   ERT       Longer version of ERS. Exact restart from startup, default 2 month + 1 month (ERS with info DBUG = 1).

   IRT       Exact restart from startup, (default 4 days + 7 days) with restart from interim file.

   ERIO      Exact restart from startup with different IO file types, (default 6 days + 5 days).

   ERR       Exact restart from startup with resubmit, (default 4 days + 3 days).

   ERRI      Exact restart from startup with resubmit, (default 4 days + 3 days). Tests incomplete logs option for st_archive.

   ERI       hybrid/branch/exact restart test, default (by default STOP_N is 22 days)
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

   ERP       PES counts hybrid (OPENMP/MPI) restart bit for bit test from startup, (default 6 days + 5 days).
              Initial PES set up out of the box
              Do an 11 day initial test - write a restart at day 6.     (file suffix base)
              Half the number of tasks and threads for each component.
              Do a 5 day restart test starting from restart at day 6. (file suffix rest)
              Compare component history files '.base' and '.rest' at day 11.
              This is just like an ERS test but the tasks/threading counts are modified on restart

   PEA       Single PE bit for bit test (default 5 days)
              Do an initial run on 1 PE with mpi library.     (file suffix: base)
              Do the same run on 1 PE with mpiserial library. (file suffix: mpiserial)
              Compare base and mpiserial.

   PEM       Modified PE counts for MPI(NTASKS) bit for bit test (default 5 days)
              Do an initial run with default PE layout                                     (file suffix: base)
              Do another initial run with modified PE layout (NTASKS_XXX => NTASKS_XXX/2)  (file suffix: modpes)
              Compare base and modpes

   PET       Modified threading OPENMP bit for bit test (default 5 days)
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

   REP       Reproducibility: Two identical initial runs are bit for bit. (default 5 days)

   SBN       Smoke build-namelist test (just run preview_namelist and check_input_data).

   SMS       Smoke test (default 5 days)
              Do a 5 day initial test that runs to completing without error. (file suffix: base)

   SEQ       Different sequencing bit for bit test. (default 10 days)
              Do an initial run test with out-of-box PE-layout. (file suffix: base)
              Do a second run where all root pes are at pe-0.   (file suffix: seq)
              Compare base and seq.

   DAE       Data assimilation test, default 1 day, two DA cycles, no data modification.

   PRE       Pause-resume test: by default a bit for bit test of pause-resume cycling.
              Default 5 hours, five pause/resume cycles, no data modification.
             |

============ =====================================================================================

The tests run for a default length indicated above, will use default pelayouts for the case
on the machine the test runs on and its default coupler and MPI library. Its possible to modify
elements of the test through a test type modifier.

.. _MODIFIERS:

-------------------
Testtype Modifiers
-------------------

============ =====================================================================================
MODIFIERS    Description
============ =====================================================================================
   _C#       Set number of instances to # and use the multi driver (can't use with _N).

   _CG       CALENDAR set to "GREGORIAN"

   _D        XML variable DEBUG set to "TRUE"

   _I        Marker to distinguish tests with same name - ignored.

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

    CIMEROOT/scripts/create_test ERP_D.ne4pg2_oQU480.F2010

This will run the ERP test for 3 days instead of the default 11 days::

    CIMEROOT/scripts/create_test ERP_Ld3.ne4pg2_oQU480.F2010

You can combine testtype modifiers::

    CIMEROOT/scripts/create_test ERP_D_Ld3.ne4pg2_oQU480.F2010

-------------------
Test Case Modifiers
-------------------

.. _GROUP-TESTMODS:

create_test runs with out-of-the-box compsets and grid sets. Sometimes you may want to run a test with
modification to a namelist or other setting without creating an entire compset. CCS provides the testmods
capability for this situation.

A testmod is a string at the end of the full testname (including machine and compiler)
with the form GROUP-TESTMODS which are parsed by create_test as follows:


============ =====================================================================================
TESTMOD      Description
============ =====================================================================================
GROUP        Define the subdirectory of testmods_dirs and the parent directory of various testmods.

TESTMODS     A subdirectory of GROUP containing files which set non-default values
             of the set-up and run-time variables via namelists or xml_change commands.
             Example:

              | GROUP-TESTMODS = cam-outfrq9s points to
              |    $cesm/components/cam/cime_config/testdefs/testmods_dirs/cam/outfrq9s
              | while allactive-defaultio points to
              |    $cesm/cime_config/testmods_dirs/allactive/defaultio

============ =====================================================================================

For example, the ERP test for an E3SM F-case can be modified to use a different radiation scheme::

    CIMEROOT/scripts/create_test ERP_D_Ld3.ne4pg2_oQU480.F2010.pm-cpu_intel.eam-rrtmgp

This tells create_test to look in $e3sm/components/eam/cime_config/testdefs/testmods_dirs/eam/rrtmpg
where it finds the following lines in the shell_commands file::

    #!/bin/bash
    ./xmlchange --append CAM_CONFIG_OPTS='-rad rrtmgp'

These commands are applied after the testcase is created and case.setup is called.

The contents of each testmods directory can include
::

    user_nl_$components    namelist variable=value pairs
    shell_commands         xmlchange commands
    user_mods              a list of other GROUP-TESTMODS which should be imported
                           but at a lower precedence than the local testmods.

eam/cime_config/testdefs/testmods_dirs/eam contains modifications for eam in an F-case test.  You
might make a directory called eam/cime_config/testdefs/testmods_dirs/elm to modify the land model
in an F-case test.

The "rrtmpg" directory contains the actual testmods to apply.
Note; do not use '-' in the testmods directory name because it has a special meaning to create_test.

========================
Test progress and output
========================

Each test run by `create_test <../Tools_user/create_test.html>`_  includes the following mandatory steps:

* CREATE_NEWCASE: creating the create
* XML: xml changes to case based on test settings
* SETUP: setup case (case.setup)
* SHAREDLIB_BUILD: build sharedlibs
* MODEL_BUILD: build module (case.build)
* SUBMIT: submit test (case.submit)
* RUN: run test test

And the following optional phases:

* NLCOMP: Compare case namelists against baselines
* THROUGHPUT: Compare throughput against baseline throughput
* MEMCOMP: Compare memory usage against baseline memory usage
* MEMLEAK: Check for memleak
* COMPARE: Used to track test-specific comparions, for example, an ERS test would have a COMPARE_base_rest phase representing the check that the base result matched the restart result.
* GENERATE: Generate baseline results
* BASELINE: Compare results against baselines

Each phase within the test may be in one of the following states:

* PASS: The phase was executed successfully
* FAIL: We attempted to execute this phase, but it failed. If this phase is mandatory, no further progress will be made on this test. A detailed explanation of the failure should be in TestStatus.log.
* PEND: This phase will be run or is currently running but not complete

======================================================
Running multiple tests and other command line examples
======================================================

Multiple tests can be run by listing all of the test names on the command line::

  $CIMEROOT/scripts/create_test  $test_name  $test_name2

or by putting the test names into a file, one name per line::

  $CIMEROOT/scripts/create_test -f $file_of_test_names

To run a test with a non-default compiler::

  ./create_test SMS.f19_f19.A --compiler intel

To run a test with baseline comparisons against baseline name 'master'::

  ./create_test SMS.f19_f19.A -c -b master

To run a test and update baselines with baseline name 'master'::

  ./create_test SMS.f19_f19.A -g -b master

To run a test with a non-default test-id::

  ./create_test SMS.f19_f19.A -t my_test_id

To run a test and use a non-default test-root for your case dir::

  ./create_test SMS.f19_f19.A -t $test_root

To run a test and use and put case, build, and run dirs all in the same root::

  ./create_test SMS.f19_f19.A --output-root $output_root

To run a test and force it to go into a certain batch queue::

  ./create_test SMS.f19_f19.A -q myqueue

The Case Control System supports more sophisticated ways to specify a suite of tests and
how they should be run.  One approach uses XML files and the other uses python dictionaries.

===========================
Test control with XML files
===========================
.. _query_testlists:

A pre-defined suite of tests can by run using the ``--xml`` options to create_test,
which harvest test names from testlist*.xml files.
As described in https://github.com/ESCOMP/ctsm/wiki/System-Testing-Guide,
to determine what pre-defined test suites are available and what tests they contain,
you can run query_testlists_.

Test suites are retrieved in create_test via 3 selection attributes::

    --xml-category your_category   The test category.
    --xml-machine  your_machine    The machine.
    --xml-compiler your_compiler   The compiler.

| If none of these 3 are used, the default values are 'none'.
| If any of them are used, the default for the unused options is 'all'.
| Existing values of these attributes can be seen by running query_testlists_.

The search for test names can be restricted to a single test list using::

    --xml-testlist your_testlist

Omitting this results in searching all testlists listed in::

    cime/config/{cesm,e3sm}/config_files.xml

**$CIMEROOT/scripts/query_testlists** gathers descriptions of the tests and testlists available
in the XML format, the components, and projects.

The ``--xml-{compiler,machine,category,testlist}`` arguments can be used
as in create_test (above) to focus the search.
The 'category' descriptor of a test can be used to run a group of associated tests at the same time.
The available categories, with the tests they encompass, can be listed by::

   ./query_testlists --define-testtypes

The ``--show-options`` argument does the same, but displays the 'options' defined for the tests,
such as queue, walltime, etc..

Adding a test requires first deciding which compset will be tested
and then finding the appropriate testlist_$component.xml file::

    components/$component/cime_config/testdefs/
       testlist_$component.xml
       testmods_dirs/$component/{TESTMODS1,TESTMODS2,...}
    cime_config/
       testlist_allactive.xml
       testmods_dirs/allactive/{defaultio,...}

You can optionally add testmods for that test in the testmods_dirs.
Testlists and testmods live in different paths for cime, drv, and components.

If this test will only be run as a single test, you can now create a test name
and follow the individual_ test instructions for create_test.

=====================================
Test control with python dictionaries
=====================================
.. _`python dict testing`:

One can also define suites of tests in a file called tests.py typically located in $MODEL/cime_config/tests.py

To run a test suite called e3sm_developer::

  ./create_test e3sm_developer

One can exclude a specific test from a suite::

  ./create_test e3sm_developer ^SMS.f19_f19.A

See create_test -h for the full list of options
`

To add a test, open the MODEL/cime_config/tests.py file, you'll see a python dict at the top
of the file called _TESTS, find the test category you want to
change in this dict and add your testcase to the list.  Note the
comment at the top of this file indicating that you add a test with
this format: test>.<grid>.<compset>, and then there is a second
argument for mods.  Machine and compiler are added later depending on where
create_test is invoked and its arguments.

Existing tests can be listed using the cime/CIME/Tools/list_e3sm_tests script.

For example::

  /list_e3sm_tests -t compsets e3sm_developer

Will list all the compsets tested in the e3sm_developer test suite.

============================
Create_test output
============================

Interpreting test output is pretty easy. Looking at an example::

  % ./create_test SMS.f19_f19.A

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

You can see that `create_test <../Tools_user/create_test.html>`_  informs the user of the case directory and of the progress and duration
of the various test phases.

The $CASEDIR for the test will be created in $CIME_OUTPUT_ROOT.  The name will be of the form::

     TESTTYPE[_MODIFIERS].GRID.COMPSET.MACHINE_COMPILER[.GROUP-TESTMODS].YYYYMMDD_HHMMSS_hash

If MODIFIERS or GROUP-TESTMODS are used, those will be included in the test output directory name.  THe
extra string with YYYYMMDD_HHMMSS_hash is the testid and used to distinquish mulitple runs of the
same test.  That string
can be replaced with the --test-id argument to create_test.

For a test, the $CASEDIR will have $EXEROOT and $RUNDIR as subdirectories.

The current state of a test is represented in the file $CASEDIR/TestStatus.  Example output::

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

All other stdout output from the CIME case control system produced by running this test will
be put in the file $CASEDIR/TestStatus.log

A cs.status.$testid script will also be put in the test root. This script will allow you to see the

==============================
Baselines and Baseline Testing
==============================
.. _`Baselines`:

A big part of testing is managing your baselines (sometimes called gold results) and doing additional tests against
the baseline. The baseline for a test will be copy of the (history) files created in the run of the test.

create_test can
be asked to perform bit-for-bit comparisons between the files generated by the current run of the test and
the files stored in the baseline.  They must be bit-for-bit identical for the baseline test to pass.

baseline testing adds an additional
test criteria to the one that comes from the test type and is used as a way to guard against unintentionaly
changing the results from a determinstic climate model.

-------------------
Creating a baseline
-------------------
.. _`Creating a baseline`:

A baseline can be generated by passing ``-g`` to `create_test <../Tools_user/create_test.html>`_. There
are additional options to control generating baselines.::

  ./scripts/create_test -b master -g SMS.ne30_f19_g16_rx1.A

--------------------
Comparing a baseline
--------------------
.. _`Comparing a baseline`:

Comparing the output of a test to a baseline is achieved by passing ``-c`` to `create_test <../Tools_user/create_test.html>`_.::

  ./scripts/create_test -b master -c SMS.ne30_f19_g16_rx1.A

Suppose you accidentally changed something in the source code that does not cause the model to crash but
does cause it to change the answers it produces.  In this case, the SMS test would pass (it still runs) but the
comparison with baselines would FAIL (answers are not bit-for-bit identical to the baseline) and so the test
as a whole would FAIL.

------------------
Managing baselines
------------------
.. _`Managing baselines`:

If you intended to change the answers, you need to update the baseline with new files.  This is referred to 
as "blessing" the test.
This is done with the `bless_test_results <../Tools_user/bless_test_results.html>`_ tool. The tool provides the ability to bless different features of the baseline. The currently supported features are namelist files, history files, and performance metrics. The performance metrics are separated into throughput and memory usage.

The following command can be used to compare a test to a baseline and bless an update to the history file.::

  ./CIME/Tools/bless_test_results -b master --hist-only SMS.ne30_f19_g16_rx1.A

The `compare_test_results <../Tools_user/compare_test_results.html>_` tool can be used to quickly compare tests to baselines and report any `diffs`.::

  ./CIME/Tools/compare_test_results -b master SMS.ne30_f19_g16_rx1.A

---------------------
Performance baselines
---------------------
.. _`Performance baselines`:
By default performance baselines are generated by parsing the coupler log and comparing the throughput in SYPD (Simulated Years Per Day) and the memory usage high water.

This can be customized by creating a python module under ``$DRIVER_ROOT/cime_config/customize``. There are four hooks that can be used to customize the generation and comparison.

- perf_get_throughput
- perf_get_memory
- perf_compare_throughput_baseline
- perf_compare_memory_baseline

..
  TODO need to add api docs and link
The following pseudo code is an example of this customization.::

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
