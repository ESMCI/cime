import os
import sys

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "lib"))
sys.path.insert(0, CIMEROOT)

import pytest

from CIME import utils
from CIME.tests.base import BaseTestCase
from CIME.XML.machines import Machines

def pytest_addoption(parser):
    parser.addoption("--fast", action="store_true",
                     help="Skip full system tests, which saves a lot of time")

    parser.addoption("--no-batch", action="store_true",
                     help="Do not submit jobs to batch system, run locally."
                     " If false, will default to machine setting.")

    parser.addoption("--no-fortran-run", action="store_true",
                     help="Do not run any fortran jobs. Implies --fast"
                     " Used for github actions")

    parser.addoption("--no-cmake", action="store_true",
                     help="Do not run cmake tests")

    parser.addoption("--no-teardown", action="store_true",
                     help="Do not delete directories left behind by testing")

    parser.addoption("--machine",
                     help="Select a specific machine setting for cime", default=None)

    parser.addoption("--compiler",
                     help="Select a specific compiler setting for cime", default=None)

    parser.addoption( "--mpilib",
                     help="Select a specific compiler setting for cime", default=None)

    parser.addoption( "--test-root",
                     help="Select a specific test root for all cases created by the testing", default=None)

    parser.addoption("--timeout", type=int,
                     help="Select a specific timeout for all tests", default=None)


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
