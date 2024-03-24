#!/usr/bin/env python3

"""
Script containing CIME python regression test suite. This suite should be run
to confirm overall CIME correctness.
"""

import glob, os, re, shutil, signal, sys, tempfile, threading, time, logging, unittest, getpass, filecmp, time, atexit, functools

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, CIMEROOT)

from xml.etree.ElementTree import ParseError

import subprocess, argparse

subprocess.call('/bin/rm -f $(find . -name "*.pyc")', shell=True, cwd=CIMEROOT)
import stat as osstat

import collections

from CIME.utils import (
    run_cmd,
    run_cmd_no_fail,
    get_lids,
    get_current_commit,
    safe_copy,
    CIMEError,
    get_cime_root,
    get_src_root,
    Timeout,
    import_from_file,
    get_model,
)
import CIME.test_scheduler, CIME.wait_for_tests
from CIME import get_tests
from CIME.test_scheduler import TestScheduler
from CIME.XML.env_run import EnvRun
from CIME.XML.machines import Machines
from CIME.XML.files import Files
from CIME.case import Case
from CIME.code_checker import check_code, get_all_checkable_files
from CIME.test_status import *
from CIME.provenance import get_test_success, save_test_success
from CIME import utils
from CIME.tests.base import BaseTestCase
from CIME.config import Config

os.environ["CIME_GLOBAL_WALLTIME"] = "0:05:00"

TEST_RESULT = None


def write_provenance_info(machine, test_compiler, test_mpilib, test_root):
    curr_commit = get_current_commit(repo=CIMEROOT)
    logging.info("Testing commit %s" % curr_commit)
    cime_model = get_model()
    logging.info("Using cime_model = %s" % cime_model)
    logging.info("Testing machine = %s" % machine.get_machine_name())
    if test_compiler is not None:
        logging.info("Testing compiler = %s" % test_compiler)
    if test_mpilib is not None:
        logging.info("Testing mpilib = %s" % test_mpilib)
    logging.info("Test root: %s" % test_root)
    logging.info("Test driver: %s" % CIME.utils.get_cime_default_driver())
    logging.info("Python version {}\n".format(sys.version))


def cleanup(test_root):
    if (
        os.path.exists(test_root)
        and TEST_RESULT is not None
        and TEST_RESULT.wasSuccessful()
    ):
        testreporter = os.path.join(test_root, "testreporter")
        files = os.listdir(test_root)
        if len(files) == 1 and os.path.isfile(testreporter):
            os.unlink(testreporter)
        if not os.listdir(test_root):
            print("All pass, removing directory:", test_root)
            os.rmdir(test_root)


def setup_arguments(parser):
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip full system tests, which saves a lot of time",
    )

    parser.add_argument(
        "--no-batch",
        action="store_true",
        help="Do not submit jobs to batch system, run locally."
        " If false, will default to machine setting.",
    )

    parser.add_argument(
        "--no-fortran-run",
        action="store_true",
        help="Do not run any fortran jobs. Implies --fast" " Used for github actions",
    )

    parser.add_argument(
        "--no-cmake", action="store_true", help="Do not run cmake tests"
    )

    parser.add_argument(
        "--no-teardown",
        action="store_true",
        help="Do not delete directories left behind by testing",
    )

    parser.add_argument(
        "--machine", help="Select a specific machine setting for cime", default=None
    )

    parser.add_argument(
        "--compiler", help="Select a specific compiler setting for cime", default=None
    )

    parser.add_argument(
        "--mpilib", help="Select a specific compiler setting for cime", default=None
    )

    parser.add_argument(
        "--test-root",
        help="Select a specific test root for all cases created by the testing",
        default=None,
    )

    parser.add_argument(
        "--timeout",
        type=int,
        help="Select a specific timeout for all tests",
        default=None,
    )


def configure_tests(
    timeout,
    no_fortran_run,
    fast,
    no_batch,
    no_cmake,
    no_teardown,
    machine,
    compiler,
    mpilib,
    test_root,
    **kwargs
):
    config = CIME.utils.get_cime_config()

    customize_path = os.path.join(utils.get_src_root(), "cime_config", "customize")
    Config.load(customize_path)

    if timeout:
        BaseTestCase.GLOBAL_TIMEOUT = str(timeout)

    BaseTestCase.NO_FORTRAN_RUN = no_fortran_run or False
    BaseTestCase.FAST_ONLY = fast or no_fortran_run
    BaseTestCase.NO_BATCH = no_batch or False
    BaseTestCase.NO_CMAKE = no_cmake or False
    BaseTestCase.NO_TEARDOWN = no_teardown or False

    # make sure we have default values
    MACHINE = None
    TEST_COMPILER = None
    TEST_MPILIB = None

    if machine is not None:
        MACHINE = Machines(machine=machine)
        os.environ["CIME_MACHINE"] = machine
    elif "CIME_MACHINE" in os.environ:
        MACHINE = Machines(machine=os.environ["CIME_MACHINE"])
    elif config.has_option("create_test", "MACHINE"):
        MACHINE = Machines(machine=config.get("create_test", "MACHINE"))
    elif config.has_option("main", "MACHINE"):
        MACHINE = Machines(machine=config.get("main", "MACHINE"))
    else:
        MACHINE = Machines()

    BaseTestCase.MACHINE = MACHINE

    if compiler is not None:
        TEST_COMPILER = compiler
    elif config.has_option("create_test", "COMPILER"):
        TEST_COMPILER = config.get("create_test", "COMPILER")
    elif config.has_option("main", "COMPILER"):
        TEST_COMPILER = config.get("main", "COMPILER")

    BaseTestCase.TEST_COMPILER = TEST_COMPILER

    if mpilib is not None:
        TEST_MPILIB = mpilib
    elif config.has_option("create_test", "MPILIB"):
        TEST_MPILIB = config.get("create_test", "MPILIB")
    elif config.has_option("main", "MPILIB"):
        TEST_MPILIB = config.get("main", "MPILIB")

    BaseTestCase.TEST_MPILIB = TEST_MPILIB

    if test_root is not None:
        TEST_ROOT = test_root
    elif config.has_option("create_test", "TEST_ROOT"):
        TEST_ROOT = config.get("create_test", "TEST_ROOT")
    else:
        TEST_ROOT = os.path.join(
            MACHINE.get_value("CIME_OUTPUT_ROOT"),
            "scripts_regression_test.%s" % CIME.utils.get_timestamp(),
        )

    BaseTestCase.TEST_ROOT = TEST_ROOT

    write_provenance_info(MACHINE, TEST_COMPILER, TEST_MPILIB, TEST_ROOT)

    atexit.register(functools.partial(cleanup, TEST_ROOT))


def _main_func(description):
    help_str = """
{0} [TEST] [TEST]
OR
{0} --help

\033[1mEXAMPLES:\033[0m
    \033[1;32m# Run the full suite \033[0m
    > {0}

    \033[1;32m# Run single test file (with or without extension) \033[0m
    > {0} test_unit_doctest

    \033[1;32m# Run single test class from a test file \033[0m
    > {0} test_unit_doctest.TestDocs

    \033[1;32m# Run single test case from a test class \033[0m
    > {0} test_unit_doctest.TestDocs.test_lib_docs
""".format(
        os.path.basename(sys.argv[0])
    )

    parser = argparse.ArgumentParser(
        usage=help_str,
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    setup_arguments(parser)

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--silent", action="store_true", help="Disable all logging")

    parser.add_argument(
        "tests", nargs="*", help="Specific tests to run e.g. test_unit*"
    )

    ns, args = parser.parse_known_args()

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = args

    utils.configure_logging(ns.verbose, ns.debug, ns.silent)

    configure_tests(**vars(ns))

    os.chdir(CIMEROOT)

    if len(ns.tests) == 0:
        test_root = os.path.join(CIMEROOT, "CIME", "tests")

        test_suite = unittest.defaultTestLoader.discover(test_root)
    else:
        # Fixes handling shell expansion e.g. test_unit_*, by removing python extension
        tests = [x.replace(".py", "").replace("/", ".") for x in ns.tests]

        # Try to load tests by just names
        test_suite = unittest.defaultTestLoader.loadTestsFromNames(tests)

    test_runner = unittest.TextTestRunner(verbosity=2)

    global TEST_RESULT

    TEST_RESULT = test_runner.run(test_suite)

    # Implements same behavior as unittesst.main
    # https://github.com/python/cpython/blob/b6d68aa08baebb753534a26d537ac3c0d2c21c79/Lib/unittest/main.py#L272-L273
    sys.exit(not TEST_RESULT.wasSuccessful())


if __name__ == "__main__":
    _main_func(__doc__)
