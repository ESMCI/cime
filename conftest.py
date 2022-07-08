import os
import sys

CIMEROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, CIMEROOT)

import pytest

from CIME import utils
from CIME.config import Config
from CIME.tests import scripts_regression_tests

os.environ["CIME_GLOBAL_WALLTIME"] = "0:05:00"


def pytest_addoption(parser):
    # set addoption as add_argument to use common argument setup
    # pytest's addoption has same signature as add_argument
    setattr(parser, "add_argument", parser.addoption)

    scripts_regression_tests.setup_arguments(parser)

    # verbose and debug flags already exist
    parser.addoption("--silent", action="store_true", help="Disable all logging")


def pytest_configure(config):
    kwargs = vars(config.option)

    utils.configure_logging(kwargs["verbose"], kwargs["debug"], kwargs["silent"])

    scripts_regression_tests.configure_tests(**kwargs)


@pytest.fixture(scope="module", autouse=True)
def setup(pytestconfig):
    # ensure we start from CIMEROOT for each module
    os.chdir(CIMEROOT)

    srcroot = utils.get_src_root()

    customize_path = os.path.join(srcroot, "cime_config", "customize")

    if os.path.exists(customize_path):
        Config.instance().load(customize_path)

    # ensure GLOABL is reset
    utils.GLOBAL = {}
