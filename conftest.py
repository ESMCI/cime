import atexit
import os
import sys
import logging
import functools

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "lib"))
sys.path.insert(0, CIMEROOT)

import pytest

from CIME import utils
from CIME.tests import scripts_regression_tests
from CIME.tests.base import BaseTestCase
from CIME.XML.machines import Machines

os.environ["CIME_GLOBAL_WALLTIME"] = "0:05:00"


def write_provenance_info(machine, test_compiler, test_mpilib, test_root):
    curr_commit = utils.get_current_commit(repo=CIMEROOT)
    logging.info("\nTesting commit %s" % curr_commit)
    cime_model = utils.get_model()
    logging.info("Using cime_model = %s" % cime_model)
    logging.info("Testing machine = %s" % machine)
    if test_compiler is not None:
        logging.info("Testing compiler = %s"% test_compiler)
    if test_mpilib is not None:
        logging.info("Testing mpilib = %s"% test_mpilib)
    logging.info("Test root: %s" % test_root)
    logging.info("Test driver: %s" % utils.get_cime_default_driver())
    logging.info("Python version {}\n".format(sys.version))


def cleanup(test_root):
    if os.path.exists(test_root):
        testreporter = os.path.join(test_root,"testreporter")
        files = os.listdir(test_root)
        if len(files)==1 and os.path.isfile(testreporter):
            os.unlink(testreporter)
        if not os.listdir(test_root):
            print("All pass, removing directory:", test_root)
            os.rmdir(test_root)


def pytest_addoption(parser):
    setattr(parser, "add_argument", parser.addoption)

    scripts_regression_tests.configure_args(parser)


@pytest.fixture(scope="session", autouse=True)
def setup(pytestconfig):
    config = utils.get_cime_config()

    timeout = pytestconfig.getoption("timeout")

    if timeout:
        BaseTestCase.GLOBAL_TIMEOUT = str(timeout)

    BaseTestCase.NO_FORTRAN_RUN = pytestconfig.getoption("no_fortran_run", False)
    BaseTestCase.FAST_ONLY = pytestconfig.getoption("fast") or BaseTestCase.NO_FORTRAN_RUN
    BaseTestCase.NO_BATCH = pytestconfig.getoption("no_batch", False)
    BaseTestCase.NO_CMAKE = pytestconfig.getoption("no_cmake", False)
    BaseTestCase.NO_TEARDOWN = pytestconfig.getoption("no_teardown", False)

    os.chdir(CIMEROOT)

    machine = pytestconfig.getoption("machine")
    compiler = pytestconfig.getoption("compiler")
    mpilib = pytestconfig.getoption("mpilib")
    test_root = pytestconfig.getoption("test_root")

    if machine is not None:
        MACHINE = Machines(machine=machine)
    elif config.has_option("create_test", "MACHINE"):
        MACHINE = Machines(config.get("create_test", "MACHINE"))
    elif config.has_option("main", "MACHINE"):
        MACHINE = Machines(config.get("main", "MACHINE"))
    else:
        MACHINE = Machines()

    BaseTestCase.MACHINE = MACHINE

    if compiler is not None:
        TEST_COMPILER = compiler
    elif config.has_option("create_test", "COMPILER"):
        TEST_COMPILER = config.get("create_test", "COMPILER")
    elif config.has_option("main", "COMPILER"):
        TEST_COMPILER = config.get("main", "COMPILER")
    else:
        TEST_COMPILER = MACHINE.get_default_compiler()

    BaseTestCase.TEST_COMPILER = TEST_COMPILER

    if mpilib is not None:
        TEST_MPILIB = mpilib
    elif config.has_option("create_test", "MPILIB"):
        TEST_MPILIB = config.get("create_test", "MPILIB")
    elif config.has_option("main", "MPILIB"):
        TEST_MPILIB = config.get("main", "MPILIB")
    else:
        TEST_MPILIB = MACHINE.get_default_MPIlib()

    BaseTestCase.TEST_MPILIB = TEST_MPILIB

    if test_root is not None:
        TEST_ROOT = test_root
    elif config.has_option("create_test", "TEST_ROOT"):
        TEST_ROOT = config.get("create_test", "TEST_ROOT")
    else:
        TEST_ROOT = os.path.join(MACHINE.get_value("CIME_OUTPUT_ROOT"),
                                 "scripts_regression_test.%s"% utils.get_timestamp())

    BaseTestCase.TEST_ROOT = TEST_ROOT

    write_provenance_info(MACHINE, TEST_COMPILER, TEST_MPILIB, TEST_ROOT)

    atexit.register(functools.partial(cleanup, TEST_ROOT))
