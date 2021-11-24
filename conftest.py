import os
import sys

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "lib"))
sys.path.insert(0, CIMEROOT)

import pytest

from CIME.tests import scripts_regression_tests

os.environ["CIME_GLOBAL_WALLTIME"] = "0:05:00"


def pytest_addoption(parser):
    # set addoption as add_argument to use common argument setup
    # pytest's addoption has same signature as add_argument
    setattr(parser, "add_argument", parser.addoption)

    scripts_regression_tests.setup_arguments(parser)


@pytest.fixture(scope="session", autouse=True)
def setup(pytestconfig):
    kwargs = vars(pytestconfig.option)

    scripts_regression_tests.configure_tests(**kwargs)

    os.chdir(CIMEROOT)
